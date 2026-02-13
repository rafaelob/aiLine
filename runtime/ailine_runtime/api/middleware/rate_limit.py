"""Simple in-memory rate limiter using sliding window counters.

Pre-MVP: in-memory only. Production: swap for Redis-backed implementation.
Configurable via AILINE_RATE_LIMIT_RPM (requests per minute, default 60).

Security note: This middleware rate-limits by client IP address (or
authenticated teacher_id when available from tenant context). It uses a
sliding window counter approach for accuracy without the memory overhead
of per-request timestamps.

Excluded paths: /health and /health/ready are exempt from rate limiting
to avoid interfering with orchestration liveness/readiness probes.
"""

from __future__ import annotations

import os
import time
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ...shared.tenant import try_get_current_teacher_id

logger = structlog.get_logger("ailine.middleware.rate_limit")

# Paths excluded from rate limiting (health probes and metrics must never be throttled).
_EXCLUDED_PATHS = frozenset({"/health", "/health/ready", "/metrics"})

# Periodic cleanup interval: every N requests, purge expired entries.
_CLEANUP_INTERVAL = 100


class _SlidingWindowCounter:
    """Sliding window counter for a single client.

    Tracks request counts in the current and previous window to
    approximate a true sliding window without storing individual
    timestamps.
    """

    __slots__ = ("prev_count", "curr_count", "prev_window_start", "curr_window_start")

    def __init__(self) -> None:
        self.prev_count: int = 0
        self.curr_count: int = 0
        self.prev_window_start: float = 0.0
        self.curr_window_start: float = 0.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory per-client rate limiter using sliding window counters.

    Identifies clients by teacher_id (if authenticated via tenant context
    middleware) or by IP address. Returns 429 Too Many Requests with a
    Retry-After header when the limit is exceeded.

    Response headers on every request:
    - X-RateLimit-Limit: the configured RPM
    - X-RateLimit-Remaining: estimated remaining requests in the window
    - X-RateLimit-Reset: Unix timestamp when the current window resets
    """

    def __init__(self, app: object, *, rpm: int | None = None) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._rpm = rpm if rpm is not None else int(
            os.getenv("AILINE_RATE_LIMIT_RPM", "60")
        )
        self._window_seconds = 60.0
        # client_key -> _SlidingWindowCounter
        self._counters: dict[str, _SlidingWindowCounter] = {}
        self._request_count = 0

    @property
    def rpm(self) -> int:
        """The configured requests-per-minute limit."""
        return self._rpm

    def _client_key(self, request: Request) -> str:
        """Determine the rate-limit key for the request.

        Uses the authenticated teacher_id if available (set by
        TenantContextMiddleware earlier in the stack), otherwise falls
        back to the client IP address.
        """
        teacher_id = try_get_current_teacher_id()
        if teacher_id is not None:
            return f"tid:{teacher_id}"
        # Use the first entry in X-Forwarded-For if present, otherwise
        # fall back to request.client.host.
        forwarded = request.headers.get("X-Forwarded-For", "").strip()
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        if request.client is not None:
            return f"ip:{request.client.host}"
        return "ip:unknown"

    def _get_sliding_count(
        self, counter: _SlidingWindowCounter, now: float
    ) -> float:
        """Compute the weighted sliding window request count."""
        window = self._window_seconds
        window_start = now - (now % window)

        # Roll the window if needed.
        if counter.curr_window_start != window_start:
            if counter.curr_window_start == window_start - window:
                # Previous window just ended; rotate.
                counter.prev_count = counter.curr_count
                counter.prev_window_start = counter.curr_window_start
            else:
                # Gap of more than one window; reset both.
                counter.prev_count = 0
                counter.prev_window_start = window_start - window
            counter.curr_count = 0
            counter.curr_window_start = window_start

        # Weighted estimate: fraction of previous window still relevant.
        elapsed_in_window = now - window_start
        prev_weight = 1.0 - (elapsed_in_window / window)
        return counter.prev_count * prev_weight + counter.curr_count

    def _maybe_cleanup(self, now: float) -> None:
        """Purge counters that have been idle for more than 2 windows."""
        self._request_count += 1
        if self._request_count % _CLEANUP_INTERVAL != 0:
            return
        cutoff = now - 2 * self._window_seconds
        stale_keys = [
            k
            for k, v in self._counters.items()
            if v.curr_window_start < cutoff
        ]
        for k in stale_keys:
            del self._counters[k]
        if stale_keys:
            logger.debug(
                "rate_limit_cleanup",
                purged=len(stale_keys),
                remaining=len(self._counters),
            )

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Exclude health probes from rate limiting.
        path = request.url.path
        if path in _EXCLUDED_PATHS:
            return await call_next(request)

        now = time.monotonic()
        client_key = self._client_key(request)

        # Get or create counter for this client.
        counter = self._counters.get(client_key)
        if counter is None:
            counter = _SlidingWindowCounter()
            counter.curr_window_start = now - (now % self._window_seconds)
            self._counters[client_key] = counter

        estimated_count = self._get_sliding_count(counter, now)

        # Compute reset timestamp (wall clock).
        window_start = now - (now % self._window_seconds)
        reset_at = time.time() + (self._window_seconds - (now - window_start))

        if estimated_count >= self._rpm:
            # Rate limit exceeded.
            retry_after = int(self._window_seconds - (now - window_start)) + 1
            logger.warning(
                "rate_limit_exceeded",
                client_key=client_key,
                estimated_count=round(estimated_count, 1),
                limit=self._rpm,
            )
            self._maybe_cleanup(now)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please retry later."},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self._rpm),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at)),
                },
            )

        # Accept the request and increment the counter.
        counter.curr_count += 1
        remaining = max(0, int(self._rpm - estimated_count - 1))

        self._maybe_cleanup(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_at))
        return response
