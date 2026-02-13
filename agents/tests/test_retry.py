"""Tests for the async retry helper with exponential backoff."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ailine_agents.workflows._retry import _is_transient, with_retry


class TestIsTransient:
    """_is_transient() classifies exceptions as transient or non-transient."""

    def test_connection_error(self) -> None:
        assert _is_transient(ConnectionError("connection refused")) is True

    def test_timeout_error(self) -> None:
        assert _is_transient(TimeoutError("timed out")) is True

    def test_value_error_not_transient(self) -> None:
        assert _is_transient(ValueError("bad value")) is False

    def test_key_error_not_transient(self) -> None:
        assert _is_transient(KeyError("missing key")) is False

    def test_runtime_error_not_transient(self) -> None:
        assert _is_transient(RuntimeError("something broke")) is False

    def test_httpx_status_429(self) -> None:
        """httpx.HTTPStatusError with 429 is transient."""
        exc = type("HTTPStatusError", (Exception,), {})()
        response = MagicMock()
        response.status_code = 429
        exc.response = response
        assert _is_transient(exc) is True

    def test_httpx_status_500(self) -> None:
        exc = type("HTTPStatusError", (Exception,), {})()
        response = MagicMock()
        response.status_code = 500
        exc.response = response
        assert _is_transient(exc) is True

    def test_httpx_status_502(self) -> None:
        exc = type("HTTPStatusError", (Exception,), {})()
        response = MagicMock()
        response.status_code = 502
        exc.response = response
        assert _is_transient(exc) is True

    def test_httpx_status_503(self) -> None:
        exc = type("HTTPStatusError", (Exception,), {})()
        response = MagicMock()
        response.status_code = 503
        exc.response = response
        assert _is_transient(exc) is True

    def test_httpx_status_400_not_transient(self) -> None:
        exc = type("HTTPStatusError", (Exception,), {})()
        response = MagicMock()
        response.status_code = 400
        exc.response = response
        assert _is_transient(exc) is False

    def test_httpx_status_401_not_transient(self) -> None:
        exc = type("HTTPStatusError", (Exception,), {})()
        response = MagicMock()
        response.status_code = 401
        exc.response = response
        assert _is_transient(exc) is False

    def test_rate_limit_error(self) -> None:
        exc = type("RateLimitError", (Exception,), {})("rate limited")
        assert _is_transient(exc) is True

    def test_internal_server_error(self) -> None:
        exc = type("InternalServerError", (Exception,), {})("internal")
        assert _is_transient(exc) is True

    def test_api_connection_error(self) -> None:
        exc = type("APIConnectionError", (Exception,), {})("conn err")
        assert _is_transient(exc) is True

    def test_chained_cause_transient(self) -> None:
        """Exception with a transient __cause__ is transient."""
        outer = RuntimeError("wrapper")
        outer.__cause__ = ConnectionError("root cause")
        assert _is_transient(outer) is True

    def test_chained_cause_not_transient(self) -> None:
        outer = RuntimeError("wrapper")
        outer.__cause__ = ValueError("not transient")
        assert _is_transient(outer) is False


class TestWithRetry:
    """with_retry() retries transient errors with backoff."""

    async def test_success_first_attempt(self) -> None:
        fn = AsyncMock(return_value=42)
        result = await with_retry(fn, max_attempts=3)
        assert result == 42
        fn.assert_awaited_once()

    async def test_retries_on_transient_then_succeeds(self) -> None:
        fn = AsyncMock(side_effect=[ConnectionError("fail"), 42])
        result = await with_retry(
            fn,
            max_attempts=3,
            initial_delay=0.01,
            backoff_factor=1.0,
        )
        assert result == 42
        assert fn.await_count == 2

    async def test_retries_exhausted(self) -> None:
        fn = AsyncMock(side_effect=ConnectionError("always fails"))
        with pytest.raises(ConnectionError, match="always fails"):
            await with_retry(
                fn,
                max_attempts=3,
                initial_delay=0.01,
                backoff_factor=1.0,
            )
        assert fn.await_count == 3

    async def test_non_transient_raises_immediately(self) -> None:
        fn = AsyncMock(side_effect=ValueError("bad input"))
        with pytest.raises(ValueError, match="bad input"):
            await with_retry(
                fn,
                max_attempts=3,
                initial_delay=0.01,
            )
        # Should not retry on non-transient errors
        fn.assert_awaited_once()

    async def test_timeout_error_retried(self) -> None:
        fn = AsyncMock(side_effect=[TimeoutError(), "ok"])
        result = await with_retry(
            fn,
            max_attempts=3,
            initial_delay=0.01,
            backoff_factor=1.0,
        )
        assert result == "ok"
        assert fn.await_count == 2

    async def test_backoff_delay_increases(self) -> None:
        """Verify delays increase with backoff_factor."""
        fn = AsyncMock(side_effect=[
            ConnectionError("1"),
            ConnectionError("2"),
            "success",
        ])
        with patch("ailine_agents.workflows._retry.asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            result = await with_retry(
                fn,
                max_attempts=3,
                initial_delay=1.0,
                backoff_factor=2.0,
            )
        assert result == "success"
        # First retry: delay=1.0, second retry: delay=2.0
        assert mock_sleep.await_count == 2
        assert mock_sleep.call_args_list[0][0][0] == 1.0
        assert mock_sleep.call_args_list[1][0][0] == 2.0

    async def test_single_attempt_raises_immediately(self) -> None:
        fn = AsyncMock(side_effect=ConnectionError("fail"))
        with pytest.raises(ConnectionError):
            await with_retry(fn, max_attempts=1, initial_delay=0.01)
        fn.assert_awaited_once()

    async def test_custom_operation_name_in_logs(self) -> None:
        """Verify operation_name is passed through (no assertion on log content, just no crash)."""
        fn = AsyncMock(side_effect=[ConnectionError("fail"), "ok"])
        result = await with_retry(
            fn,
            max_attempts=2,
            initial_delay=0.01,
            operation_name="my_custom_op",
            run_id="test-123",
        )
        assert result == "ok"
