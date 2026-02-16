"""Per-tenant token usage tracking and cost guards.

Tracks token consumption per tenant with daily caps and per-minute
request rate limits. In-memory implementation suitable for single-process
deployments; swap for Redis-backed storage in multi-process production.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class TenantBudget:
    """Budget configuration for a single tenant."""

    daily_token_cap: int = 100_000
    per_minute_request_cap: int = 20


@dataclass
class UsageTracker:
    """In-memory per-tenant usage tracker.

    Thread-safe. Tracks daily token usage and per-minute request counts.
    """

    _token_usage: dict[str, dict[str, int]] = field(default_factory=dict)
    _request_timestamps: dict[str, list[float]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def _today_key(self) -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def record_tokens(self, tenant_id: str, tokens: int) -> None:
        """Record token usage for a tenant."""
        day = self._today_key()
        with self._lock:
            if tenant_id not in self._token_usage:
                self._token_usage[tenant_id] = {}
            usage = self._token_usage[tenant_id]
            usage[day] = usage.get(day, 0) + tokens

    def record_request(self, tenant_id: str) -> None:
        """Record a request timestamp for rate limiting."""
        now = time.monotonic()
        with self._lock:
            if tenant_id not in self._request_timestamps:
                self._request_timestamps[tenant_id] = []
            self._request_timestamps[tenant_id].append(now)

    def check_budget(self, tenant_id: str, budget: TenantBudget) -> tuple[bool, str]:
        """Check if tenant is within budget.

        Returns (allowed, reason). If not allowed, reason explains why.
        """
        day = self._today_key()
        now = time.monotonic()
        cutoff = now - 60.0

        with self._lock:
            # Check daily token cap
            tenant_usage = self._token_usage.get(tenant_id, {})
            daily_tokens = tenant_usage.get(day, 0)
            if daily_tokens >= budget.daily_token_cap:
                return False, (
                    f"Daily token cap exceeded: {daily_tokens}/{budget.daily_token_cap}"
                )

            # Check per-minute request rate
            timestamps = self._request_timestamps.get(tenant_id, [])
            # Prune old timestamps
            recent = [t for t in timestamps if t > cutoff]
            self._request_timestamps[tenant_id] = recent

            if len(recent) >= budget.per_minute_request_cap:
                return False, (
                    f"Per-minute request cap exceeded: {len(recent)}/{budget.per_minute_request_cap}"
                )

        return True, ""

    def get_usage(self, tenant_id: str) -> dict[str, int | float]:
        """Get current usage stats for a tenant."""
        day = self._today_key()
        now = time.monotonic()
        cutoff = now - 60.0

        with self._lock:
            daily_tokens = self._token_usage.get(tenant_id, {}).get(day, 0)
            timestamps = self._request_timestamps.get(tenant_id, [])
            recent_requests = len([t for t in timestamps if t > cutoff])

        return {
            "daily_tokens": daily_tokens,
            "recent_requests_per_minute": recent_requests,
        }

    def remaining_tokens(self, tenant_id: str, budget: TenantBudget) -> int:
        """Return how many tokens remain in today's budget."""
        day = self._today_key()
        with self._lock:
            used = self._token_usage.get(tenant_id, {}).get(day, 0)
        return max(0, budget.daily_token_cap - used)

    def clear(self) -> None:
        """Clear all tracked usage (useful for testing)."""
        with self._lock:
            self._token_usage.clear()
            self._request_timestamps.clear()
