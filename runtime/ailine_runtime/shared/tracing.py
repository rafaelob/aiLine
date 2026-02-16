"""OpenTelemetry tracing setup for AiLine runtime.

Provides optional OTEL tracing when the ``otel`` extra is installed.
When OTEL packages are not available, all functions are safe no-ops.

Tracing coverage:
- FastAPI request handling (auto-instrumented)
- SQLAlchemy DB queries (auto-instrumented)
- LLM calls (manual spans via ``trace_llm_call``)
- LangGraph node execution (manual spans via ``trace_pipeline_node``)
- Tool calls (manual spans via ``trace_tool_call``)

Configuration via environment variables:
- ``OTEL_SERVICE_NAME``: Service name (default: "ailine-runtime")
- ``OTEL_EXPORTER_OTLP_ENDPOINT``: OTLP gRPC endpoint (default: console)
- ``AILINE_OTEL_ENABLED``: Set to "true" to enable (default: false)
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import structlog

_log = structlog.get_logger("ailine.tracing")

# Lazy-loaded OTEL references
_tracer: Any = None
_initialized = False


def _is_enabled() -> bool:
    return os.getenv("AILINE_OTEL_ENABLED", "").lower() in ("true", "1", "yes")


def init_tracing(*, service_name: str = "ailine-runtime") -> bool:
    """Initialize OpenTelemetry tracing.

    Returns True if tracing was successfully initialized, False otherwise.
    Safe to call multiple times (idempotent).
    """
    global _tracer, _initialized

    if _initialized:
        return _tracer is not None

    _initialized = True

    if not _is_enabled():
        _log.info(
            "tracing_disabled", msg="AILINE_OTEL_ENABLED is not set, tracing disabled"
        )
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        _log.warning(
            "tracing_unavailable",
            msg="OpenTelemetry SDK not installed. Install with: pip install ailine-runtime[otel]",
        )
        return False

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # Configure exporter
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            _log.info("tracing_otlp_configured", endpoint=otlp_endpoint)
        except ImportError:
            _log.warning("tracing_otlp_unavailable", msg="OTLP exporter not installed")
    else:
        # Console exporter for development
        try:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter

            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            _log.info("tracing_console_configured")
        except ImportError:
            pass

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("ailine.runtime")

    _log.info("tracing_initialized", service_name=service_name)
    return True


def instrument_fastapi(app: Any) -> None:
    """Auto-instrument a FastAPI app with OTEL spans."""
    if not _is_enabled():
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        _log.info("tracing_fastapi_instrumented")
    except ImportError:
        _log.debug(
            "tracing_fastapi_skip", msg="FastAPI OTEL instrumentation not installed"
        )


def instrument_sqlalchemy(engine: Any) -> None:
    """Auto-instrument a SQLAlchemy engine with OTEL spans."""
    if not _is_enabled():
        return
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(engine=engine)
        _log.info("tracing_sqlalchemy_instrumented")
    except ImportError:
        _log.debug(
            "tracing_sqlalchemy_skip",
            msg="SQLAlchemy OTEL instrumentation not installed",
        )


def get_tracer() -> Any:
    """Return the OTEL tracer, or None if tracing is not initialized."""
    return _tracer


@contextmanager
def trace_llm_call(
    *,
    provider: str,
    model: str,
    tier: str,
) -> Iterator[dict[str, Any]]:
    """Context manager that creates an OTEL span for an LLM call.

    Yields a mutable dict where callers can set ``tokens_in``,
    ``tokens_out``, ``latency_ms``, and ``error`` after the call.

    Usage::

        with trace_llm_call(provider="anthropic", model="haiku", tier="fast") as span_data:
            result = await llm.generate(...)
            span_data["tokens_in"] = result.input_tokens
            span_data["tokens_out"] = result.output_tokens
    """
    span_data: dict[str, Any] = {
        "provider": provider,
        "model": model,
        "tier": tier,
    }

    if _tracer is None:
        yield span_data
        return

    with _tracer.start_as_current_span(
        "llm.call",
        attributes={
            "llm.provider": provider,
            "llm.model": model,
            "llm.tier": tier,
        },
    ) as span:
        try:
            yield span_data
            # Set attributes from span_data after the call
            if "tokens_in" in span_data:
                span.set_attribute("llm.tokens.input", span_data["tokens_in"])
            if "tokens_out" in span_data:
                span.set_attribute("llm.tokens.output", span_data["tokens_out"])
            if "latency_ms" in span_data:
                span.set_attribute("llm.latency_ms", span_data["latency_ms"])
        except Exception as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(exc)[:500])
            raise


@contextmanager
def trace_pipeline_node(
    *,
    node_name: str,
    run_id: str,
) -> Iterator[dict[str, Any]]:
    """Context manager that creates an OTEL span for a LangGraph node execution."""
    span_data: dict[str, Any] = {"node": node_name, "run_id": run_id}

    if _tracer is None:
        yield span_data
        return

    with _tracer.start_as_current_span(
        f"pipeline.{node_name}",
        attributes={
            "pipeline.node": node_name,
            "pipeline.run_id": run_id,
        },
    ) as span:
        try:
            yield span_data
            if "status" in span_data:
                span.set_attribute("pipeline.status", span_data["status"])
        except Exception as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(exc)[:500])
            raise


@contextmanager
def trace_tool_call(
    *,
    tool_name: str,
) -> Iterator[dict[str, Any]]:
    """Context manager that creates an OTEL span for a tool call."""
    span_data: dict[str, Any] = {"tool": tool_name}

    if _tracer is None:
        yield span_data
        return

    with _tracer.start_as_current_span(
        f"tool.{tool_name}",
        attributes={"tool.name": tool_name},
    ) as span:
        try:
            yield span_data
            if "latency_ms" in span_data:
                span.set_attribute("tool.latency_ms", span_data["latency_ms"])
        except Exception as exc:
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(exc)[:500])
            raise
