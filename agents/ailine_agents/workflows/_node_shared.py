"""Shared helpers for LangGraph plan workflow node functions.

Contains timeout checking, model selection, error handling,
retry orchestration, and success logging used across all nodes.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from ailine_runtime.api.streaming.events import SSEEvent, SSEEventEmitter, SSEEventType
from ailine_runtime.shared.observability import log_event, log_pipeline_stage

from ..deps import AgentDeps
from ..model_selection.bridge import PydanticAIModelSelector
from ..resilience import CircuitOpenError
from ._retry import with_retry
from ._sse_helpers import try_emit
from ._trace_capture import capture_node_trace

__all__ = [
    "WorkflowTimeoutError",
    "_check_timeout",
    "_handle_node_failure",
    "_log_node_success",
    "_run_agent_with_resilience",
    "_select_model",
]

log = structlog.get_logger(__name__)


class WorkflowTimeoutError(Exception):
    """Raised when a workflow exceeds its maximum allowed duration."""


def _check_timeout(state: Any, deps: AgentDeps, stage: str) -> None:
    """Check if the workflow has exceeded its time budget."""
    started_at = state.get("started_at")
    if started_at is None:
        return
    elapsed = time.monotonic() - started_at
    if elapsed > deps.max_workflow_duration_seconds:
        run_id = state.get("run_id", "")
        log.error(
            "workflow.timeout",
            run_id=run_id,
            stage=stage,
            elapsed_seconds=round(elapsed, 1),
            limit_seconds=deps.max_workflow_duration_seconds,
        )
        raise WorkflowTimeoutError(
            f"Workflow timed out after {elapsed:.1f}s (limit: {deps.max_workflow_duration_seconds}s) at stage '{stage}'"
        )


def _select_model(
    model_selector: PydanticAIModelSelector | None,
) -> tuple[Any, str]:
    """Select model from SmartRouter or return defaults."""
    if model_selector:
        model_override = model_selector.select_model(tier="primary")
        model_name = str(model_override) if model_override else "default"
        return model_override, model_name
    return None, "default"


# ---------------------------------------------------------------------------
# Shared error-handling helper for LLM agent nodes
# ---------------------------------------------------------------------------


async def _handle_node_failure(
    exc: Exception,
    *,
    deps: AgentDeps,
    stage: str,
    run_id: str,
    stage_start: float,
    emitter: SSEEventEmitter | None,
    writer: Callable[[SSEEvent], None] | None,
) -> None:
    """Record failure metrics, emit SSE, and capture trace for a failed node."""
    deps.circuit_breaker.record_failure()
    duration_ms = (time.monotonic() - stage_start) * 1000
    log_event(f"{stage}.failed", run_id=run_id, error=str(exc), duration_ms=round(duration_ms, 2))
    log_pipeline_stage(
        stage=stage,
        run_id=run_id,
        duration_ms=duration_ms,
        status="failed",
        metadata={"error": str(exc)},
    )
    try_emit(emitter, writer, SSEEventType.STAGE_FAILED, stage, {"error": str(exc)})
    await capture_node_trace(
        run_id=run_id,
        node_name=stage,
        status="failed",
        time_ms=duration_ms,
        error=str(exc),
    )


async def _run_agent_with_resilience(
    *,
    agent_fn: Callable[[], Awaitable[Any]],
    deps: AgentDeps,
    stage: str,
    run_id: str,
    stage_start: float,
    emitter: SSEEventEmitter | None,
    writer: Callable[[SSEEvent], None] | None,
    max_attempts: int = 3,
) -> Any:
    """Run an agent callable with retry and circuit breaker recording.

    Returns the result on success. Raises on failure after recording metrics.
    """
    if not deps.circuit_breaker.check():
        log_event(f"{stage}.circuit_open", run_id=run_id)
        try_emit(
            emitter,
            writer,
            SSEEventType.STAGE_FAILED,
            stage,
            {
                "error": "Circuit breaker open -- LLM service unavailable",
            },
        )
        raise CircuitOpenError("LLM circuit breaker is open")

    try:
        result = await with_retry(
            agent_fn,
            max_attempts=max_attempts,
            initial_delay=1.0,
            backoff_factor=2.0,
            operation_name=f"{stage}.run",
            run_id=run_id,
        )
        deps.circuit_breaker.record_success()
        return result
    except CircuitOpenError:
        raise
    except Exception as exc:
        await _handle_node_failure(
            exc,
            deps=deps,
            stage=stage,
            run_id=run_id,
            stage_start=stage_start,
            emitter=emitter,
            writer=writer,
        )
        raise


def _log_node_success(
    *,
    stage: str,
    run_id: str,
    model_name: str,
    duration_ms: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Log success event and pipeline stage for a completed node."""
    log_event(
        f"{stage}.complete",
        run_id=run_id,
        stage=stage,
        model=model_name,
        duration_ms=round(duration_ms, 2),
    )
    log_pipeline_stage(
        stage=stage,
        run_id=run_id,
        duration_ms=duration_ms,
        status="success",
        metadata={"model": model_name, **(metadata or {})},
    )
