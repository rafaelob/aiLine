"""Resilience primitives for the AiLine agent framework.

CircuitBreaker: prevents cascading failures by tracking consecutive LLM
call failures and temporarily blocking new calls when the threshold is
exceeded. After a cooldown period, a single probe call is allowed to test
recovery (half-open state).

IdempotencyGuard: prevents duplicate workflow runs from concurrent
requests with the same idempotency key.
"""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any

import structlog

log = structlog.get_logger(__name__)


class CircuitBreaker:
    """Thread-safe circuit breaker for LLM call protection.

    States:
    - CLOSED:    Normal operation. Failures are counted.
    - OPEN:      Too many failures. Calls are blocked until cooldown expires.
    - HALF-OPEN: Cooldown expired. One probe call is allowed.

    After a successful call in any state, the failure count resets.
    After a failure in HALF-OPEN, the circuit reopens for another cooldown.
    """

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        cooldown_seconds: float = 60.0,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._failure_count = 0
        self._circuit_open_until: float | None = None
        self._lock = threading.Lock()

    @property
    def failure_count(self) -> int:
        """Current consecutive failure count."""
        return self._failure_count

    @property
    def is_open(self) -> bool:
        """True if the circuit is open and blocking calls."""
        with self._lock:
            return self._is_open_locked()

    def _is_open_locked(self) -> bool:
        """Check if circuit is open (must hold _lock)."""
        if self._circuit_open_until is None:
            return False
        # Cooldown expired -- transition to half-open
        return time.monotonic() < self._circuit_open_until

    def check(self) -> bool:
        """Check if a call is allowed.

        Returns True if the call can proceed, False if the circuit is open.
        """
        with self._lock:
            if self._is_open_locked():
                log.warning(
                    "circuit_breaker.blocked",
                    failure_count=self._failure_count,
                    open_until=self._circuit_open_until,
                    remaining_seconds=round((self._circuit_open_until or 0) - time.monotonic(), 1),
                )
                return False
            return True

    def record_success(self) -> None:
        """Record a successful call -- resets the failure counter."""
        with self._lock:
            prev_count = self._failure_count
            self._failure_count = 0
            self._circuit_open_until = None
            if prev_count > 0:
                log.info(
                    "circuit_breaker.reset",
                    previous_failures=prev_count,
                )

    def record_failure(self) -> None:
        """Record a failed call. Opens the circuit if threshold is reached."""
        with self._lock:
            self._failure_count += 1
            if self._failure_count >= self._failure_threshold:
                self._circuit_open_until = time.monotonic() + self._cooldown_seconds
                log.error(
                    "circuit_breaker.opened",
                    failure_count=self._failure_count,
                    cooldown_seconds=self._cooldown_seconds,
                    open_until=self._circuit_open_until,
                )

    def reset(self) -> None:
        """Force-reset the circuit breaker (useful for testing)."""
        with self._lock:
            self._failure_count = 0
            self._circuit_open_until = None


class CircuitOpenError(Exception):
    """Raised when the circuit breaker is open and blocking calls."""

    def __init__(self, message: str = "Circuit breaker is open") -> None:
        super().__init__(message)


class IdempotencyGuard:
    """Prevents duplicate concurrent workflow runs with the same key.

    Thread-safe. Keys are tracked in memory (suitable for single-process
    deployments; for multi-process, use Redis or a database).

    TTL and max_size prevent unbounded memory growth:
    - Entries older than ``ttl_seconds`` are evicted on access.
    - When the results dict exceeds ``max_size``, the oldest entries
      are evicted first.
    """

    def __init__(
        self,
        *,
        ttl_seconds: float = 300.0,
        max_size: int = 1000,
    ) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size
        self._in_progress: dict[str, asyncio.Event] = {}
        self._results: dict[str, Any] = {}
        self._timestamps: dict[str, float] = {}
        self._lock = threading.Lock()

    def _evict_expired_locked(self) -> None:
        """Remove entries older than TTL (must hold _lock)."""
        cutoff = time.monotonic() - self._ttl_seconds
        expired = [k for k, ts in self._timestamps.items() if ts < cutoff]
        for k in expired:
            self._results.pop(k, None)
            self._timestamps.pop(k, None)

    def _evict_oldest_locked(self) -> None:
        """Remove oldest entries if results exceed max_size (must hold _lock)."""
        while len(self._results) > self._max_size:
            oldest_key = min(self._timestamps, key=self._timestamps.get)  # type: ignore[arg-type]
            self._results.pop(oldest_key, None)
            self._timestamps.pop(oldest_key, None)

    def try_acquire(self, key: str) -> bool:
        """Attempt to acquire a lock for the given idempotency key.

        Returns True if this is a new run (caller should proceed).
        Returns False if a run with this key is already in progress.
        """
        with self._lock:
            self._evict_expired_locked()
            if key in self._in_progress:
                return False
            self._in_progress[key] = asyncio.Event()
            return True

    def complete(self, key: str, result: Any) -> None:
        """Mark a run as completed and store its result."""
        with self._lock:
            self._results[key] = result
            self._timestamps[key] = time.monotonic()
            event = self._in_progress.pop(key, None)
            self._evict_oldest_locked()
        if event is not None:
            event.set()

    def fail(self, key: str) -> None:
        """Mark a run as failed and remove it from tracking."""
        with self._lock:
            event = self._in_progress.pop(key, None)
            self._results.pop(key, None)
            self._timestamps.pop(key, None)
        if event is not None:
            event.set()

    def get_result(self, key: str) -> tuple[bool, Any]:
        """Get the result for a completed run.

        Returns (found, result) tuple. Evicts expired entries first.
        """
        with self._lock:
            self._evict_expired_locked()
            if key in self._results:
                return True, self._results[key]
            return False, None

    def is_in_progress(self, key: str) -> bool:
        """Check if a run with this key is currently in progress."""
        with self._lock:
            return key in self._in_progress

    def clear(self) -> None:
        """Clear all tracked keys (useful for testing)."""
        with self._lock:
            self._in_progress.clear()
            self._results.clear()
            self._timestamps.clear()
