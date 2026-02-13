"""Structured observability for AiLine runtime.

Provides:
- Structured logging via structlog (JSON or console).
- Request-scoped correlation via contextvars (request_id, teacher_id).
- span_context: sync context manager for timing + structured span events.
- timed_operation: async context manager for timing async operations.
- Helpers for LLM call, tool execution, and pipeline stage logging.

No OpenTelemetry SDK dependency -- structlog structured logs are the
observability backend, consumable by any log aggregator.
"""

from __future__ import annotations

import contextvars
import logging
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import Any

import structlog

# ---------------------------------------------------------------------------
# Request-scoped correlation via contextvars
# ---------------------------------------------------------------------------

_request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "ailine_request_id", default=None
)
_teacher_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "ailine_teacher_id", default=None
)


def set_request_context(
    request_id: str,
    teacher_id: str | None = None,
) -> None:
    """Bind request-scoped correlation IDs into contextvars.

    These are automatically merged into every structlog event via
    ``structlog.contextvars.merge_contextvars``.
    """
    _request_id_var.set(request_id)
    _teacher_id_var.set(teacher_id)
    # Also bind into structlog's own contextvars so they appear in all
    # log lines produced by any logger in this async context.
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        **({"teacher_id": teacher_id} if teacher_id is not None else {}),
    )


def get_request_context() -> dict[str, str | None]:
    """Return the current request-scoped correlation fields."""
    return {
        "request_id": _request_id_var.get(),
        "teacher_id": _teacher_id_var.get(),
    }


def clear_request_context() -> None:
    """Reset request-scoped correlation (e.g. at end of request)."""
    _request_id_var.set(None)
    _teacher_id_var.set(None)
    structlog.contextvars.unbind_contextvars("request_id", "teacher_id")


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------


def configure_logging(*, json_output: bool = True, level: str = "INFO") -> None:
    """Configure structlog for structured JSON logging."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[*shared_processors, renderer],
        )
    )

    root_logger = logging.getLogger()
    # Avoid accumulating handlers on repeated calls
    if not any(
        isinstance(h, logging.StreamHandler)
        and isinstance(
            getattr(h, "formatter", None), structlog.stdlib.ProcessorFormatter
        )
        for h in root_logger.handlers
    ):
        root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger


# ---------------------------------------------------------------------------
# log_event -- enriched with request context
# ---------------------------------------------------------------------------


def log_event(name: str, **data: Any) -> None:
    """Log a pipeline event, auto-enriched with request context when available."""
    logger = get_logger("ailine.events")
    # Inject request context if not already supplied by caller
    ctx = get_request_context()
    if ctx["request_id"] is not None and "request_id" not in data:
        data["request_id"] = ctx["request_id"]
    if ctx["teacher_id"] is not None and "teacher_id" not in data:
        data["teacher_id"] = ctx["teacher_id"]
    logger.info(name, **data)


# ---------------------------------------------------------------------------
# span_context -- synchronous span tracking
# ---------------------------------------------------------------------------


@contextmanager
def span_context(
    operation: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Context manager that tracks operation timing and success/failure.

    Usage::

        with span_context("my_operation", metadata={"key": "val"}) as span:
            do_work()
        # On exit, a structured log event is emitted with duration, success, etc.

    The yielded ``span`` dict can be mutated to add extra fields that will
    appear in the final log event.
    """
    span: dict[str, Any] = {
        "operation": operation,
        "metadata": metadata or {},
    }
    start = time.monotonic()
    success = True
    error_msg: str | None = None
    try:
        yield span
    except Exception as exc:
        success = False
        error_msg = str(exc)
        raise
    finally:
        duration_ms = (time.monotonic() - start) * 1000.0
        logger = get_logger("ailine.spans")
        log_data: dict[str, Any] = {
            "operation": operation,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            **span.get("metadata", {}),
        }
        if error_msg is not None:
            log_data["error"] = error_msg
        # Include request context
        ctx = get_request_context()
        if ctx["request_id"] is not None:
            log_data["request_id"] = ctx["request_id"]
        if ctx["teacher_id"] is not None:
            log_data["teacher_id"] = ctx["teacher_id"]

        if success:
            logger.info("span.complete", **log_data)
        else:
            logger.warning("span.failed", **log_data)


# ---------------------------------------------------------------------------
# timed_operation -- async span tracking
# ---------------------------------------------------------------------------


@asynccontextmanager
async def timed_operation(
    name: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Async context manager that auto-logs timing for an operation.

    Usage::

        async with timed_operation("fetch_embeddings") as span:
            result = await fetch()
            span["metadata"]["count"] = len(result)
    """
    span: dict[str, Any] = {
        "operation": name,
        "metadata": metadata or {},
    }
    start = time.monotonic()
    success = True
    error_msg: str | None = None
    try:
        yield span
    except Exception as exc:
        success = False
        error_msg = str(exc)
        raise
    finally:
        duration_ms = (time.monotonic() - start) * 1000.0
        logger = get_logger("ailine.spans")
        log_data: dict[str, Any] = {
            "operation": name,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            **span.get("metadata", {}),
        }
        if error_msg is not None:
            log_data["error"] = error_msg
        ctx = get_request_context()
        if ctx["request_id"] is not None:
            log_data["request_id"] = ctx["request_id"]
        if ctx["teacher_id"] is not None:
            log_data["teacher_id"] = ctx["teacher_id"]

        if success:
            logger.info("span.complete", **log_data)
        else:
            logger.warning("span.failed", **log_data)


# ---------------------------------------------------------------------------
# LLM call instrumentation
# ---------------------------------------------------------------------------


def log_llm_call(
    *,
    provider: str,
    model: str,
    tier: str,
    latency_ms: float,
    tokens_est: int,
    success: bool,
    error: str | None = None,
) -> None:
    """Emit a structured log event for an LLM invocation.

    Designed to be called from LLM adapter code after each generate/stream
    call completes (or fails).
    """
    logger = get_logger("ailine.llm")
    log_data: dict[str, Any] = {
        "provider": provider,
        "model": model,
        "tier": tier,
        "latency_ms": round(latency_ms, 2),
        "tokens_est": tokens_est,
        "success": success,
    }
    if error is not None:
        log_data["error"] = error
    ctx = get_request_context()
    if ctx["request_id"] is not None:
        log_data["request_id"] = ctx["request_id"]
    if ctx["teacher_id"] is not None:
        log_data["teacher_id"] = ctx["teacher_id"]

    if success:
        logger.info("llm.call", **log_data)
    else:
        logger.warning("llm.call.failed", **log_data)


# ---------------------------------------------------------------------------
# Tool execution instrumentation
# ---------------------------------------------------------------------------


def log_tool_execution(
    *,
    tool_name: str,
    latency_ms: float,
    success: bool,
    error: str | None = None,
) -> None:
    """Emit a structured log event for a tool execution."""
    logger = get_logger("ailine.tools")
    log_data: dict[str, Any] = {
        "tool_name": tool_name,
        "latency_ms": round(latency_ms, 2),
        "success": success,
    }
    if error is not None:
        log_data["error"] = error
    ctx = get_request_context()
    if ctx["request_id"] is not None:
        log_data["request_id"] = ctx["request_id"]
    if ctx["teacher_id"] is not None:
        log_data["teacher_id"] = ctx["teacher_id"]

    if success:
        logger.info("tool.exec", **log_data)
    else:
        logger.warning("tool.exec.failed", **log_data)


# ---------------------------------------------------------------------------
# Pipeline stage metrics
# ---------------------------------------------------------------------------


def log_pipeline_stage(
    *,
    stage: str,
    run_id: str,
    duration_ms: float,
    status: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Emit a structured log event for a LangGraph pipeline node execution.

    Args:
        stage: Node/stage name (e.g. "planner", "validate", "executor").
        run_id: Pipeline run correlation ID.
        duration_ms: Wall-clock time for the stage.
        status: Outcome string (e.g. "success", "failed", "skipped").
        metadata: Additional stage-specific data.
    """
    logger = get_logger("ailine.pipeline")
    log_data: dict[str, Any] = {
        "stage": stage,
        "run_id": run_id,
        "duration_ms": round(duration_ms, 2),
        "status": status,
        **(metadata or {}),
    }
    ctx = get_request_context()
    if ctx["request_id"] is not None:
        log_data["request_id"] = ctx["request_id"]
    if ctx["teacher_id"] is not None:
        log_data["teacher_id"] = ctx["teacher_id"]

    if status == "failed":
        logger.warning("pipeline.stage", **log_data)
    else:
        logger.info("pipeline.stage", **log_data)
