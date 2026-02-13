"""Tests for shared.observability -- structured logging, spans, and instrumentation."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from ailine_runtime.shared.observability import (
    clear_request_context,
    configure_logging,
    get_logger,
    get_request_context,
    log_event,
    log_llm_call,
    log_pipeline_stage,
    log_tool_execution,
    set_request_context,
    span_context,
    timed_operation,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_request_context():
    """Ensure each test starts with a clean request context."""
    clear_request_context()
    yield
    clear_request_context()


# ---------------------------------------------------------------------------
# configure_logging
# ---------------------------------------------------------------------------


class TestConfigureLogging:
    def test_json_mode(self):
        configure_logging(json_output=True, level="DEBUG")

    def test_console_mode(self):
        configure_logging(json_output=False, level="INFO")


# ---------------------------------------------------------------------------
# get_logger
# ---------------------------------------------------------------------------


class TestGetLogger:
    def test_returns_bound_logger(self):
        logger = get_logger("test.module")
        assert logger is not None


# ---------------------------------------------------------------------------
# Request context (contextvars)
# ---------------------------------------------------------------------------


class TestRequestContext:
    def test_default_context_is_none(self):
        ctx = get_request_context()
        assert ctx["request_id"] is None
        assert ctx["teacher_id"] is None

    def test_set_and_get(self):
        set_request_context("req-123", teacher_id="t-456")
        ctx = get_request_context()
        assert ctx["request_id"] == "req-123"
        assert ctx["teacher_id"] == "t-456"

    def test_set_without_teacher(self):
        set_request_context("req-789")
        ctx = get_request_context()
        assert ctx["request_id"] == "req-789"
        assert ctx["teacher_id"] is None

    def test_clear_resets(self):
        set_request_context("req-abc", teacher_id="t-def")
        clear_request_context()
        ctx = get_request_context()
        assert ctx["request_id"] is None
        assert ctx["teacher_id"] is None


# ---------------------------------------------------------------------------
# log_event
# ---------------------------------------------------------------------------


class TestLogEvent:
    def test_does_not_raise(self):
        configure_logging(json_output=False, level="DEBUG")
        log_event("test_event", foo="bar", count=42)

    def test_injects_request_id(self):
        configure_logging(json_output=False, level="DEBUG")
        set_request_context("req-auto")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_event("test_inject")
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args
            assert call_kwargs.kwargs.get("request_id") == "req-auto"

    def test_does_not_overwrite_caller_request_id(self):
        """If the caller explicitly passes request_id, do not overwrite."""
        configure_logging(json_output=False, level="DEBUG")
        set_request_context("ctx-req")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_event("test_explicit", request_id="caller-req")
            mock_logger.info.assert_called_once()
            assert mock_logger.info.call_args.kwargs.get("request_id") == "caller-req"


# ---------------------------------------------------------------------------
# span_context
# ---------------------------------------------------------------------------


class TestSpanContext:
    def test_successful_span(self):
        configure_logging(json_output=False, level="DEBUG")
        with span_context("test_op") as span:
            span["metadata"]["extra"] = "data"

    def test_span_yields_mutable_dict(self):
        with span_context("test_op") as span:
            assert isinstance(span, dict)
            assert span["operation"] == "test_op"
            span["metadata"]["custom"] = True

    def test_span_with_metadata(self):
        with span_context("test_op", metadata={"key": "val"}) as span:
            assert span["metadata"]["key"] == "val"

    def test_span_on_exception(self):
        with pytest.raises(ValueError, match="boom"), span_context("failing_op"):
            raise ValueError("boom")

    def test_span_includes_request_context(self):
        configure_logging(json_output=False, level="DEBUG")
        set_request_context("req-span", teacher_id="t-span")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            with span_context("ctx_op"):
                pass
            mock_logger.info.assert_called()
            call_kwargs = mock_logger.info.call_args.kwargs
            assert call_kwargs.get("request_id") == "req-span"
            assert call_kwargs.get("teacher_id") == "t-span"

    def test_span_logs_duration(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            with span_context("timed_op"):
                pass
            call_kwargs = mock_logger.info.call_args.kwargs
            assert "duration_ms" in call_kwargs
            assert isinstance(call_kwargs["duration_ms"], float)
            assert call_kwargs["duration_ms"] >= 0

    def test_failed_span_logs_warning(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            with pytest.raises(RuntimeError), span_context("bad_op"):
                raise RuntimeError("fail")
            mock_logger.warning.assert_called_once()
            call_kwargs = mock_logger.warning.call_args.kwargs
            assert call_kwargs["success"] is False
            assert "fail" in call_kwargs["error"]


# ---------------------------------------------------------------------------
# timed_operation (async)
# ---------------------------------------------------------------------------


class TestTimedOperation:
    @pytest.mark.asyncio
    async def test_successful_async_span(self):
        configure_logging(json_output=False, level="DEBUG")
        async with timed_operation("async_op") as span:
            span["metadata"]["count"] = 5

    @pytest.mark.asyncio
    async def test_async_span_on_exception(self):
        with pytest.raises(ValueError, match="async_boom"):
            async with timed_operation("async_fail"):
                raise ValueError("async_boom")

    @pytest.mark.asyncio
    async def test_async_span_logs_duration(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            async with timed_operation("measured_op"):
                await asyncio.sleep(0.01)
            call_kwargs = mock_logger.info.call_args.kwargs
            assert "duration_ms" in call_kwargs
            # Should be at least ~10ms (we slept 10ms)
            assert call_kwargs["duration_ms"] >= 5.0

    @pytest.mark.asyncio
    async def test_async_span_includes_request_context(self):
        configure_logging(json_output=False, level="DEBUG")
        set_request_context("req-async", teacher_id="t-async")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            async with timed_operation("ctx_async_op"):
                pass
            call_kwargs = mock_logger.info.call_args.kwargs
            assert call_kwargs.get("request_id") == "req-async"

    @pytest.mark.asyncio
    async def test_async_failed_span_logs_warning(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            with pytest.raises(RuntimeError):
                async with timed_operation("async_bad"):
                    raise RuntimeError("async_fail")
            mock_logger.warning.assert_called_once()
            call_kwargs = mock_logger.warning.call_args.kwargs
            assert call_kwargs["success"] is False


# ---------------------------------------------------------------------------
# log_llm_call
# ---------------------------------------------------------------------------


class TestLogLLMCall:
    def test_success_call(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_llm_call(
                provider="anthropic",
                model="claude-haiku-4-5-20251001",
                tier="cheap",
                latency_ms=150.456,
                tokens_est=500,
                success=True,
            )
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args.args[0] == "llm.call"
            assert call_args.kwargs["provider"] == "anthropic"
            assert call_args.kwargs["model"] == "claude-haiku-4-5-20251001"
            assert call_args.kwargs["tier"] == "cheap"
            assert call_args.kwargs["latency_ms"] == 150.46
            assert call_args.kwargs["tokens_est"] == 500
            assert call_args.kwargs["success"] is True
            assert "error" not in call_args.kwargs

    def test_failed_call(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_llm_call(
                provider="openai",
                model="gpt-4o",
                tier="middle",
                latency_ms=5000.0,
                tokens_est=0,
                success=False,
                error="timeout",
            )
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args.args[0] == "llm.call.failed"
            assert call_args.kwargs["error"] == "timeout"
            assert call_args.kwargs["success"] is False

    def test_includes_request_context(self):
        configure_logging(json_output=False, level="DEBUG")
        set_request_context("req-llm", teacher_id="t-llm")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_llm_call(
                provider="gemini",
                model="gemini-2.0-flash",
                tier="cheap",
                latency_ms=200.0,
                tokens_est=300,
                success=True,
            )
            call_kwargs = mock_logger.info.call_args.kwargs
            assert call_kwargs["request_id"] == "req-llm"
            assert call_kwargs["teacher_id"] == "t-llm"


# ---------------------------------------------------------------------------
# log_tool_execution
# ---------------------------------------------------------------------------


class TestLogToolExecution:
    def test_success(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_tool_execution(
                tool_name="rag_search",
                latency_ms=45.0,
                success=True,
            )
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args.args[0] == "tool.exec"
            assert call_args.kwargs["tool_name"] == "rag_search"
            assert call_args.kwargs["success"] is True
            assert "error" not in call_args.kwargs

    def test_failure(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_tool_execution(
                tool_name="web_search",
                latency_ms=3000.0,
                success=False,
                error="connection refused",
            )
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args.args[0] == "tool.exec.failed"
            assert call_args.kwargs["error"] == "connection refused"


# ---------------------------------------------------------------------------
# log_pipeline_stage
# ---------------------------------------------------------------------------


class TestLogPipelineStage:
    def test_success_stage(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_pipeline_stage(
                stage="planner",
                run_id="run-001",
                duration_ms=1234.5,
                status="success",
                metadata={"tokens": 800},
            )
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args.args[0] == "pipeline.stage"
            assert call_args.kwargs["stage"] == "planner"
            assert call_args.kwargs["run_id"] == "run-001"
            assert call_args.kwargs["duration_ms"] == 1234.5
            assert call_args.kwargs["status"] == "success"
            assert call_args.kwargs["tokens"] == 800

    def test_failed_stage(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_pipeline_stage(
                stage="executor",
                run_id="run-002",
                duration_ms=500.0,
                status="failed",
                metadata={"error": "LLM timeout"},
            )
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args.kwargs["status"] == "failed"

    def test_no_metadata(self):
        configure_logging(json_output=False, level="DEBUG")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_pipeline_stage(
                stage="validate",
                run_id="run-003",
                duration_ms=100.0,
                status="success",
            )
            mock_logger.info.assert_called_once()

    def test_includes_request_context(self):
        configure_logging(json_output=False, level="DEBUG")
        set_request_context("req-pipe", teacher_id="t-pipe")

        with patch("ailine_runtime.shared.observability.get_logger") as mock_gl:
            mock_logger = mock_gl.return_value
            log_pipeline_stage(
                stage="planner",
                run_id="run-004",
                duration_ms=200.0,
                status="success",
            )
            call_kwargs = mock_logger.info.call_args.kwargs
            assert call_kwargs["request_id"] == "req-pipe"
            assert call_kwargs["teacher_id"] == "t-pipe"
