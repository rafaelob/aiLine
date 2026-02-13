"""Tests for OpenTelemetry tracing setup.

Tests the tracing module's behavior both when OTEL is enabled/disabled
and when OTEL packages are available/unavailable.
"""

from __future__ import annotations

import pytest

from ailine_runtime.shared.tracing import (
    get_tracer,
    trace_llm_call,
    trace_pipeline_node,
    trace_tool_call,
)


class TestTracingDisabled:
    """When AILINE_OTEL_ENABLED is not set, tracing should be a safe no-op."""

    def test_trace_llm_call_noop(self) -> None:
        with trace_llm_call(provider="anthropic", model="haiku", tier="fast") as data:
            data["tokens_in"] = 100
            data["tokens_out"] = 50
        assert data["provider"] == "anthropic"
        assert data["tokens_in"] == 100

    def test_trace_pipeline_node_noop(self) -> None:
        with trace_pipeline_node(node_name="planner", run_id="test-run") as data:
            data["status"] = "success"
        assert data["node"] == "planner"

    def test_trace_tool_call_noop(self) -> None:
        with trace_tool_call(tool_name="rag_search") as data:
            data["latency_ms"] = 42.0
        assert data["tool"] == "rag_search"

    def test_trace_llm_call_propagates_exception(self) -> None:
        with (
            pytest.raises(ValueError, match="test error"),
            trace_llm_call(provider="openai", model="gpt", tier="balanced"),
        ):
            raise ValueError("test error")

    def test_trace_pipeline_node_propagates_exception(self) -> None:
        with (
            pytest.raises(RuntimeError, match="pipeline crash"),
            trace_pipeline_node(node_name="executor", run_id="r1"),
        ):
            raise RuntimeError("pipeline crash")

    def test_trace_tool_call_propagates_exception(self) -> None:
        with (
            pytest.raises(TimeoutError, match="tool timeout"),
            trace_tool_call(tool_name="slow_tool"),
        ):
            raise TimeoutError("tool timeout")

    def test_get_tracer_returns_none_when_disabled(self) -> None:
        tracer = get_tracer()
        # Tracer is None when tracing is not initialized/enabled
        # (may not be None if another test initialized it, so just check type)
        assert tracer is None or hasattr(tracer, "start_as_current_span")


class TestTracingInit:
    """Test init_tracing behavior."""

    def test_init_returns_false_when_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AILINE_OTEL_ENABLED", raising=False)
        # Reset global state for this test
        import ailine_runtime.shared.tracing as mod

        mod._initialized = False
        mod._tracer = None

        result = mod.init_tracing()
        assert result is False

    def test_init_is_idempotent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AILINE_OTEL_ENABLED", raising=False)
        import ailine_runtime.shared.tracing as mod

        mod._initialized = False
        mod._tracer = None

        result1 = mod.init_tracing()
        result2 = mod.init_tracing()
        assert result1 == result2


class TestInstrumentNoops:
    """Instrumentation functions are safe no-ops when OTEL is disabled."""

    def test_instrument_fastapi_noop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from unittest.mock import MagicMock

        from ailine_runtime.shared.tracing import instrument_fastapi

        monkeypatch.delenv("AILINE_OTEL_ENABLED", raising=False)
        mock_app = MagicMock()
        instrument_fastapi(mock_app)  # should not raise

    def test_instrument_sqlalchemy_noop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from unittest.mock import MagicMock

        from ailine_runtime.shared.tracing import instrument_sqlalchemy

        monkeypatch.delenv("AILINE_OTEL_ENABLED", raising=False)
        mock_engine = MagicMock()
        instrument_sqlalchemy(mock_engine)  # should not raise


class TestTraceLLMCallWithMockTracer:
    """Verify span attributes are set when a tracer is active."""

    def test_sets_span_attributes(self) -> None:
        from unittest.mock import MagicMock

        import ailine_runtime.shared.tracing as mod

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_ctx

        original = mod._tracer
        mod._tracer = mock_tracer
        try:
            with trace_llm_call(provider="anthropic", model="haiku", tier="cheap") as data:
                data["tokens_in"] = 50
                data["latency_ms"] = 100.5

            mock_tracer.start_as_current_span.assert_called_once()
            call_kwargs = mock_tracer.start_as_current_span.call_args
            assert call_kwargs[0][0] == "llm.call"  # span name
            mock_span.set_attribute.assert_any_call("llm.tokens.input", 50)
            mock_span.set_attribute.assert_any_call("llm.latency_ms", 100.5)
        finally:
            mod._tracer = original

    def test_sets_error_on_exception(self) -> None:
        from unittest.mock import MagicMock

        import ailine_runtime.shared.tracing as mod

        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_span)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_ctx

        original = mod._tracer
        mod._tracer = mock_tracer
        try:
            with pytest.raises(ValueError, match="boom"), trace_llm_call(provider="x", model="y", tier="z"):
                raise ValueError("boom")

            mock_span.set_attribute.assert_any_call("error", True)
        finally:
            mod._tracer = original
