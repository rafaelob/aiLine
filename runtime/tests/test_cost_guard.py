"""Tests for per-tenant cost guards: TenantBudget, UsageTracker."""

from __future__ import annotations

import time

from ailine_runtime.app.cost_guard import TenantBudget, UsageTracker


class TestTenantBudget:
    def test_defaults(self) -> None:
        b = TenantBudget()
        assert b.daily_token_cap == 100_000
        assert b.per_minute_request_cap == 20

    def test_custom_values(self) -> None:
        b = TenantBudget(daily_token_cap=50_000, per_minute_request_cap=10)
        assert b.daily_token_cap == 50_000
        assert b.per_minute_request_cap == 10


class TestUsageTracker:
    def test_record_and_get_usage(self) -> None:
        tracker = UsageTracker()
        tracker.record_tokens("t1", 500)
        tracker.record_tokens("t1", 300)
        usage = tracker.get_usage("t1")
        assert usage["daily_tokens"] == 800

    def test_check_budget_allowed(self) -> None:
        tracker = UsageTracker()
        budget = TenantBudget(daily_token_cap=1000, per_minute_request_cap=5)
        tracker.record_tokens("t1", 500)
        allowed, reason = tracker.check_budget("t1", budget)
        assert allowed is True
        assert reason == ""

    def test_check_budget_daily_cap_exceeded(self) -> None:
        tracker = UsageTracker()
        budget = TenantBudget(daily_token_cap=1000, per_minute_request_cap=5)
        tracker.record_tokens("t1", 1000)
        allowed, reason = tracker.check_budget("t1", budget)
        assert allowed is False
        assert "Daily token cap exceeded" in reason

    def test_check_budget_request_rate_exceeded(self) -> None:
        tracker = UsageTracker()
        budget = TenantBudget(daily_token_cap=100_000, per_minute_request_cap=3)
        for _ in range(3):
            tracker.record_request("t1")
        allowed, reason = tracker.check_budget("t1", budget)
        assert allowed is False
        assert "Per-minute request cap exceeded" in reason

    def test_old_request_timestamps_pruned(self) -> None:
        tracker = UsageTracker()
        budget = TenantBudget(daily_token_cap=100_000, per_minute_request_cap=3)

        # Simulate old timestamps (> 60s ago)
        old_time = time.monotonic() - 120.0
        tracker._request_timestamps["t1"] = [old_time, old_time + 1, old_time + 2]

        allowed, _reason = tracker.check_budget("t1", budget)
        assert allowed is True

    def test_remaining_tokens(self) -> None:
        tracker = UsageTracker()
        budget = TenantBudget(daily_token_cap=1000)
        tracker.record_tokens("t1", 400)
        assert tracker.remaining_tokens("t1", budget) == 600

    def test_remaining_tokens_at_zero(self) -> None:
        tracker = UsageTracker()
        budget = TenantBudget(daily_token_cap=500)
        tracker.record_tokens("t1", 800)
        assert tracker.remaining_tokens("t1", budget) == 0

    def test_multiple_tenants_isolated(self) -> None:
        tracker = UsageTracker()
        budget = TenantBudget(daily_token_cap=1000, per_minute_request_cap=5)
        tracker.record_tokens("t1", 1000)
        tracker.record_tokens("t2", 100)

        allowed_t1, _ = tracker.check_budget("t1", budget)
        allowed_t2, _ = tracker.check_budget("t2", budget)
        assert allowed_t1 is False
        assert allowed_t2 is True

    def test_get_usage_unknown_tenant(self) -> None:
        tracker = UsageTracker()
        usage = tracker.get_usage("nonexistent")
        assert usage["daily_tokens"] == 0
        assert usage["recent_requests_per_minute"] == 0

    def test_clear(self) -> None:
        tracker = UsageTracker()
        tracker.record_tokens("t1", 500)
        tracker.record_request("t1")
        tracker.clear()
        usage = tracker.get_usage("t1")
        assert usage["daily_tokens"] == 0
        assert usage["recent_requests_per_minute"] == 0

    def test_request_count_in_usage(self) -> None:
        tracker = UsageTracker()
        tracker.record_request("t1")
        tracker.record_request("t1")
        usage = tracker.get_usage("t1")
        assert usage["recent_requests_per_minute"] == 2
