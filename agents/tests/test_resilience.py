"""Tests for resilience primitives: CircuitBreaker and IdempotencyGuard."""

from __future__ import annotations

import time
from unittest.mock import patch

from ailine_agents.resilience import (
    CircuitBreaker,
    CircuitOpenError,
    IdempotencyGuard,
)


class TestCircuitBreaker:
    """CircuitBreaker tracks failures and blocks calls when threshold is reached."""

    def test_initial_state(self) -> None:
        cb = CircuitBreaker()
        assert cb.failure_count == 0
        assert cb.is_open is False
        assert cb.check() is True

    def test_record_success_resets(self) -> None:
        cb = CircuitBreaker(failure_threshold=5)
        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.is_open is False

    def test_opens_at_threshold(self) -> None:
        cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60.0)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is False
        assert cb.check() is True

        cb.record_failure()  # 3rd failure -> opens
        assert cb.failure_count == 3
        assert cb.is_open is True
        assert cb.check() is False

    def test_cooldown_reopens(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=1.0)
        cb.record_failure()
        cb.record_failure()  # opens circuit

        assert cb.is_open is True
        assert cb.check() is False

        # Simulate cooldown expiry by patching time.monotonic
        future_time = time.monotonic() + 2.0
        with patch("time.monotonic", return_value=future_time):
            assert cb.is_open is False
            assert cb.check() is True

    def test_success_after_half_open(self) -> None:
        """After cooldown, a success resets the circuit."""
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.01)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is True

        # Wait for cooldown
        time.sleep(0.02)
        assert cb.check() is True  # half-open

        cb.record_success()
        assert cb.failure_count == 0
        assert cb.is_open is False

    def test_failure_after_half_open_reopens(self) -> None:
        """After cooldown, a failure reopens the circuit."""
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.01)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.02)

        assert cb.check() is True  # half-open
        cb.record_failure()  # 3rd failure total, >= threshold -> reopens
        assert cb.is_open is True

    def test_reset(self) -> None:
        cb = CircuitBreaker(failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is True

        cb.reset()
        assert cb.failure_count == 0
        assert cb.is_open is False
        assert cb.check() is True

    def test_default_thresholds(self) -> None:
        cb = CircuitBreaker()
        # Default: 5 failures, 60s cooldown
        for _ in range(4):
            cb.record_failure()
        assert cb.is_open is False

        cb.record_failure()  # 5th
        assert cb.is_open is True

    def test_circuit_open_error(self) -> None:
        err = CircuitOpenError()
        assert "open" in str(err).lower()

        err_custom = CircuitOpenError("custom message")
        assert str(err_custom) == "custom message"


class TestIdempotencyGuard:
    """IdempotencyGuard prevents duplicate concurrent workflow runs."""

    def test_acquire_new_key(self) -> None:
        guard = IdempotencyGuard()
        assert guard.try_acquire("key-1") is True
        assert guard.is_in_progress("key-1") is True

    def test_acquire_duplicate_key(self) -> None:
        guard = IdempotencyGuard()
        assert guard.try_acquire("key-1") is True
        assert guard.try_acquire("key-1") is False  # duplicate

    def test_complete_releases_key(self) -> None:
        guard = IdempotencyGuard()
        guard.try_acquire("key-1")
        guard.complete("key-1", {"result": "ok"})

        assert guard.is_in_progress("key-1") is False
        found, result = guard.get_result("key-1")
        assert found is True
        assert result == {"result": "ok"}

    def test_fail_releases_key(self) -> None:
        guard = IdempotencyGuard()
        guard.try_acquire("key-1")
        guard.fail("key-1")

        assert guard.is_in_progress("key-1") is False
        found, _result = guard.get_result("key-1")
        assert found is False

    def test_get_result_unknown_key(self) -> None:
        guard = IdempotencyGuard()
        found, result = guard.get_result("nonexistent")
        assert found is False
        assert result is None

    def test_multiple_keys(self) -> None:
        guard = IdempotencyGuard()
        assert guard.try_acquire("a") is True
        assert guard.try_acquire("b") is True
        assert guard.try_acquire("a") is False
        assert guard.try_acquire("b") is False

        guard.complete("a", "result-a")
        assert guard.try_acquire("a") is True  # can re-acquire after complete

    def test_clear(self) -> None:
        guard = IdempotencyGuard()
        guard.try_acquire("key-1")
        guard.complete("key-2", "result")
        guard.clear()

        assert guard.is_in_progress("key-1") is False
        found, _ = guard.get_result("key-2")
        assert found is False

    def test_ttl_eviction(self) -> None:
        """Entries older than TTL are evicted on access."""
        guard = IdempotencyGuard(ttl_seconds=1.0)
        guard.try_acquire("k1")
        guard.complete("k1", "r1")

        # Result is available immediately
        found, result = guard.get_result("k1")
        assert found is True
        assert result == "r1"

        # Simulate time passing beyond TTL
        future = time.monotonic() + 2.0
        with patch("ailine_agents.resilience.time") as mock_time:
            mock_time.monotonic.return_value = future
            found, result = guard.get_result("k1")
            assert found is False

    def test_max_size_eviction(self) -> None:
        """When results exceed max_size, oldest entries are evicted."""
        guard = IdempotencyGuard(max_size=3, ttl_seconds=300.0)

        base = time.monotonic()
        for i in range(5):
            key = f"k{i}"
            guard.try_acquire(key)
            # Set timestamps manually to control ordering
            with guard._lock:
                guard._results[key] = f"r{i}"
                guard._timestamps[key] = base + i
                guard._in_progress.pop(key, None)

        # After adding 5, eviction in complete() leaves max_size=3
        # But since we bypassed complete(), trigger eviction manually
        guard.try_acquire("trigger")
        guard.complete("trigger", "t")

        # Oldest entries (k0, k1) should have been evicted
        # k2, k3, k4 + trigger = 4, but max_size=3 so k2 also evicted
        found_k0, _ = guard.get_result("k0")
        found_k1, _ = guard.get_result("k1")
        assert found_k0 is False
        assert found_k1 is False

    def test_max_size_eviction_on_complete(self) -> None:
        """Complete triggers eviction when max_size is exceeded."""
        guard = IdempotencyGuard(max_size=2, ttl_seconds=300.0)

        guard.try_acquire("a")
        guard.complete("a", "ra")

        guard.try_acquire("b")
        guard.complete("b", "rb")

        # Both should exist
        assert guard.get_result("a") == (True, "ra")
        assert guard.get_result("b") == (True, "rb")

        # Adding a third should evict the oldest (a)
        guard.try_acquire("c")
        guard.complete("c", "rc")

        found_a, _ = guard.get_result("a")
        assert found_a is False
        assert guard.get_result("c") == (True, "rc")

    def test_default_ttl_and_max_size(self) -> None:
        """Default TTL is 300s and max_size is 1000."""
        guard = IdempotencyGuard()
        assert guard._ttl_seconds == 300.0
        assert guard._max_size == 1000

    def test_fail_clears_timestamp(self) -> None:
        """Failing a key removes its timestamp."""
        guard = IdempotencyGuard()
        guard.try_acquire("k1")
        guard.complete("k1", "r1")
        assert "k1" in guard._timestamps

        # Re-acquire and fail
        guard.try_acquire("k1")
        guard.fail("k1")
        assert "k1" not in guard._timestamps
