"""Tests for tracing module — OTEL-enabled paths with mock tracer.

Covers the 48% uncovered lines:
- init_tracing with OTEL enabled (both OTLP and console exporter)
- init_tracing when OTEL packages are not importable
- instrument_fastapi / instrument_sqlalchemy when enabled
- trace_pipeline_node with active tracer (span attributes + error)
- trace_tool_call with active tracer (latency + error)
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

import ailine_runtime.shared.tracing as tracing_mod
from ailine_runtime.shared.tracing import (
    trace_llm_call,
    trace_pipeline_node,
    trace_tool_call,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_tracing_state():
    """Reset tracing module globals before and after each test."""
    original_tracer = tracing_mod._tracer
    original_initialized = tracing_mod._initialized
    tracing_mod._tracer = None
    tracing_mod._initialized = False
    yield
    tracing_mod._tracer = original_tracer
    tracing_mod._initialized = original_initialized


def _make_mock_tracer():
    """Create a mock tracer with a proper start_as_current_span context manager."""
    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_span)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    mock_tracer.start_as_current_span.return_value = mock_ctx
    return mock_tracer, mock_span


# ---------------------------------------------------------------------------
# init_tracing with OTEL enabled
# ---------------------------------------------------------------------------


class TestInitTracingEnabled:
    def test_init_with_otel_sdk_console(self, monkeypatch: pytest.MonkeyPatch):
        """When OTEL is enabled and SDK is available, uses console exporter."""
        monkeypatch.setenv("AILINE_OTEL_ENABLED", "true")
        monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)

        # Create comprehensive mocks for OTEL packages
        mock_trace = MagicMock()
        mock_resource = MagicMock()
        mock_sdk_trace = MagicMock()
        mock_export = MagicMock()

        mock_provider = MagicMock()
        mock_sdk_trace.TracerProvider.return_value = mock_provider
        mock_trace.get_tracer.return_value = MagicMock()

        with patch.dict(
            sys.modules,
            {
                "opentelemetry": MagicMock(trace=mock_trace),
                "opentelemetry.trace": mock_trace,
                "opentelemetry.sdk": MagicMock(),
                "opentelemetry.sdk.resources": mock_resource,
                "opentelemetry.sdk.trace": mock_sdk_trace,
                "opentelemetry.sdk.trace.export": mock_export,
            },
        ):
            result = tracing_mod.init_tracing(service_name="test-service")
            assert result is True
            mock_sdk_trace.TracerProvider.assert_called_once()
            mock_trace.set_tracer_provider.assert_called_once_with(mock_provider)

    def test_init_with_otlp_endpoint(self, monkeypatch: pytest.MonkeyPatch):
        """When OTLP endpoint is configured, uses OTLP exporter."""
        monkeypatch.setenv("AILINE_OTEL_ENABLED", "true")
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

        mock_trace = MagicMock()
        mock_resource = MagicMock()
        mock_sdk_trace = MagicMock()
        mock_export = MagicMock()
        mock_otlp_exporter = MagicMock()

        mock_provider = MagicMock()
        mock_sdk_trace.TracerProvider.return_value = mock_provider

        with patch.dict(
            sys.modules,
            {
                "opentelemetry": MagicMock(trace=mock_trace),
                "opentelemetry.trace": mock_trace,
                "opentelemetry.sdk": MagicMock(),
                "opentelemetry.sdk.resources": mock_resource,
                "opentelemetry.sdk.trace": mock_sdk_trace,
                "opentelemetry.sdk.trace.export": mock_export,
                "opentelemetry.exporter": MagicMock(),
                "opentelemetry.exporter.otlp": MagicMock(),
                "opentelemetry.exporter.otlp.proto": MagicMock(),
                "opentelemetry.exporter.otlp.proto.grpc": MagicMock(),
                "opentelemetry.exporter.otlp.proto.grpc.trace_exporter": mock_otlp_exporter,
            },
        ):
            result = tracing_mod.init_tracing()
            assert result is True

    def test_init_when_sdk_not_installed(self, monkeypatch: pytest.MonkeyPatch):
        """When OTEL SDK is not installed, returns False."""
        monkeypatch.setenv("AILINE_OTEL_ENABLED", "true")

        # Block the OTEL imports
        with patch.dict(
            sys.modules,
            {
                "opentelemetry": None,
                "opentelemetry.trace": None,
                "opentelemetry.sdk": None,
                "opentelemetry.sdk.resources": None,
                "opentelemetry.sdk.trace": None,
                "opentelemetry.sdk.trace.export": None,
            },
        ):
            result = tracing_mod.init_tracing()
            assert result is False

    def test_init_idempotent_after_success(self, monkeypatch: pytest.MonkeyPatch):
        """Second call returns cached result."""
        monkeypatch.setenv("AILINE_OTEL_ENABLED", "true")
        tracing_mod._initialized = True
        tracing_mod._tracer = MagicMock()  # Simulate previous successful init
        result = tracing_mod.init_tracing()
        assert result is True


# ---------------------------------------------------------------------------
# instrument_fastapi / instrument_sqlalchemy when enabled
# ---------------------------------------------------------------------------


class TestInstrumentEnabled:
    def test_instrument_fastapi_when_enabled(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("AILINE_OTEL_ENABLED", "true")
        mock_instrumentor = MagicMock()
        mock_fastapi_mod = MagicMock()
        mock_fastapi_mod.FastAPIInstrumentor = mock_instrumentor

        with patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation": MagicMock(),
                "opentelemetry.instrumentation.fastapi": mock_fastapi_mod,
            },
        ):
            mock_app = MagicMock()
            tracing_mod.instrument_fastapi(mock_app)
            mock_instrumentor.instrument_app.assert_called_once_with(mock_app)

    def test_instrument_fastapi_import_error(self, monkeypatch: pytest.MonkeyPatch):
        """When instrumentation package missing, should not raise."""
        monkeypatch.setenv("AILINE_OTEL_ENABLED", "true")
        with patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation.fastapi": None,
            },
        ):
            # Should not raise
            tracing_mod.instrument_fastapi(MagicMock())

    def test_instrument_sqlalchemy_when_enabled(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("AILINE_OTEL_ENABLED", "true")
        mock_instrumentor_instance = MagicMock()
        mock_instrumentor_cls = MagicMock(return_value=mock_instrumentor_instance)
        mock_sqla_mod = MagicMock()
        mock_sqla_mod.SQLAlchemyInstrumentor = mock_instrumentor_cls

        with patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation": MagicMock(),
                "opentelemetry.instrumentation.sqlalchemy": mock_sqla_mod,
            },
        ):
            mock_engine = MagicMock()
            tracing_mod.instrument_sqlalchemy(mock_engine)
            mock_instrumentor_instance.instrument.assert_called_once_with(
                engine=mock_engine
            )

    def test_instrument_sqlalchemy_import_error(self, monkeypatch: pytest.MonkeyPatch):
        """When instrumentation package missing, should not raise."""
        monkeypatch.setenv("AILINE_OTEL_ENABLED", "true")
        with patch.dict(
            sys.modules,
            {
                "opentelemetry.instrumentation.sqlalchemy": None,
            },
        ):
            tracing_mod.instrument_sqlalchemy(MagicMock())


# ---------------------------------------------------------------------------
# trace_pipeline_node with active tracer
# ---------------------------------------------------------------------------


class TestTracePipelineNodeWithTracer:
    def test_sets_status_attribute(self):
        mock_tracer, mock_span = _make_mock_tracer()
        tracing_mod._tracer = mock_tracer
        try:
            with trace_pipeline_node(node_name="planner", run_id="r1") as data:
                data["status"] = "success"
            mock_span.set_attribute.assert_any_call("pipeline.status", "success")
        finally:
            tracing_mod._tracer = None

    def test_sets_error_on_exception(self):
        mock_tracer, mock_span = _make_mock_tracer()
        tracing_mod._tracer = mock_tracer
        try:
            with pytest.raises(RuntimeError, match="node fail"):  # noqa: SIM117
                with trace_pipeline_node(node_name="executor", run_id="r2"):
                    raise RuntimeError("node fail")
            mock_span.set_attribute.assert_any_call("error", True)
            # Check error.message was set (partial match)
            error_calls = [
                c
                for c in mock_span.set_attribute.call_args_list
                if c[0][0] == "error.message"
            ]
            assert len(error_calls) == 1
            assert "node fail" in error_calls[0][0][1]
        finally:
            tracing_mod._tracer = None

    def test_span_name_includes_node(self):
        mock_tracer, _ = _make_mock_tracer()
        tracing_mod._tracer = mock_tracer
        try:
            with trace_pipeline_node(node_name="quality_gate", run_id="r3"):
                pass
            call_args = mock_tracer.start_as_current_span.call_args
            assert call_args[0][0] == "pipeline.quality_gate"
        finally:
            tracing_mod._tracer = None


# ---------------------------------------------------------------------------
# trace_tool_call with active tracer
# ---------------------------------------------------------------------------


class TestTraceToolCallWithTracer:
    def test_sets_latency_attribute(self):
        mock_tracer, mock_span = _make_mock_tracer()
        tracing_mod._tracer = mock_tracer
        try:
            with trace_tool_call(tool_name="rag_search") as data:
                data["latency_ms"] = 55.3
            mock_span.set_attribute.assert_any_call("tool.latency_ms", 55.3)
        finally:
            tracing_mod._tracer = None

    def test_sets_error_on_exception(self):
        mock_tracer, mock_span = _make_mock_tracer()
        tracing_mod._tracer = mock_tracer
        try:
            with pytest.raises(TimeoutError, match="tool timeout"), trace_tool_call(
                tool_name="slow_tool"
            ):
                raise TimeoutError("tool timeout")
            mock_span.set_attribute.assert_any_call("error", True)
        finally:
            tracing_mod._tracer = None

    def test_span_name_includes_tool(self):
        mock_tracer, _ = _make_mock_tracer()
        tracing_mod._tracer = mock_tracer
        try:
            with trace_tool_call(tool_name="embed"):
                pass
            call_args = mock_tracer.start_as_current_span.call_args
            assert call_args[0][0] == "tool.embed"
        finally:
            tracing_mod._tracer = None

    def test_no_latency_attribute_when_not_set(self):
        mock_tracer, mock_span = _make_mock_tracer()
        tracing_mod._tracer = mock_tracer
        try:
            with trace_tool_call(tool_name="quick"):
                pass
            # latency_ms should NOT be set since we didn't add it to span_data
            latency_calls = [
                c
                for c in mock_span.set_attribute.call_args_list
                if c[0][0] == "tool.latency_ms"
            ]
            assert len(latency_calls) == 0
        finally:
            tracing_mod._tracer = None


# ---------------------------------------------------------------------------
# trace_llm_call: tokens_out attribute
# ---------------------------------------------------------------------------


class TestTraceLLMCallTokensOut:
    def test_sets_tokens_out_attribute(self):
        mock_tracer, mock_span = _make_mock_tracer()
        tracing_mod._tracer = mock_tracer
        try:
            with trace_llm_call(
                provider="anthropic", model="haiku", tier="cheap"
            ) as data:
                data["tokens_out"] = 200
            mock_span.set_attribute.assert_any_call("llm.tokens.output", 200)
        finally:
            tracing_mod._tracer = None
