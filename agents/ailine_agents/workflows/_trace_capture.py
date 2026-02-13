"""Trace capture helpers for LangGraph workflow nodes.

Bridges workflow execution data into the runtime's TraceStore,
RouteRationale domain model, and OpenTelemetry spans.
"""

from __future__ import annotations

from typing import Any

# OTEL tracing -- optional; no-op when runtime tracing is unavailable
try:
    from ailine_runtime.shared.tracing import trace_pipeline_node as _trace_pipeline_node
except ImportError:
    _trace_pipeline_node = None


def build_route_rationale(
    task_type: str,
    model_name: str,
    model_selector: Any | None,
    tier: str = "primary",
) -> dict[str, Any]:
    """Build a route rationale dict for trace capture.

    Returns a dict matching RouteRationale schema, suitable for
    inclusion in NodeTrace and SSE stage.started events.
    """
    rationale: dict[str, Any] = {
        "task_type": task_type,
        "weighted_scores": {},
        "composite_score": 0.0,
        "tier": tier,
        "model_selected": model_name,
        "reason": f"Model selected for {task_type} stage",
    }

    # If the model_selector has routing metadata, include it
    if model_selector is not None:
        # The PydanticAIModelSelector wraps SmartRouter tiers
        # In MVP, all tiers map to the same model -- show weights for context
        rationale["weighted_scores"] = {
            "token": 0.25,
            "structured": 0.25,
            "tool": 0.25,
            "history": 0.15,
            "intent": 0.10,
        }
        rationale["reason"] = (
            f"SmartRouter selected '{tier}' tier -> {model_name} "
            f"(weights: 0.25/0.25/0.25/0.15/0.10)"
        )

    return rationale


def _emit_otel_node_span(
    *,
    run_id: str,
    node_name: str,
    status: str,
    time_ms: float,
    quality_score: int | None = None,
    error: str | None = None,
) -> None:
    """Emit a post-hoc OTEL span for a completed pipeline node.

    Creates a brief span with attributes recording the node outcome.
    Safe no-op when tracing is unavailable or disabled.
    """
    if _trace_pipeline_node is None:
        return
    try:
        with _trace_pipeline_node(node_name=node_name, run_id=run_id) as span_data:
            span_data["status"] = status
            span_data["time_ms"] = time_ms
            if quality_score is not None:
                span_data["quality_score"] = quality_score
            if error:
                span_data["error"] = error
    except Exception:
        # Never let tracing break the pipeline
        pass


async def capture_node_trace(
    run_id: str,
    node_name: str,
    status: str,
    time_ms: float,
    *,
    inputs_summary: dict[str, Any] | None = None,
    outputs_summary: dict[str, Any] | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    quality_score: int | None = None,
    route_rationale: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Capture a node trace into the TraceStore.

    Safely imports from runtime; no-ops if TraceStore unavailable
    (e.g. in isolated agent testing without the runtime package).
    """
    try:
        from ailine_runtime.domain.entities.trace import NodeTrace, RouteRationale
        from ailine_runtime.shared.trace_store import get_trace_store

        store = get_trace_store()

        rationale_obj = None
        if route_rationale is not None:
            rationale_obj = RouteRationale(**route_rationale)

        node_trace = NodeTrace(
            node=node_name,
            status=status,
            time_ms=round(time_ms, 2),
            inputs_summary=inputs_summary or {},
            outputs_summary=outputs_summary or {},
            tool_calls=tool_calls or [],
            quality_score=quality_score,
            route_rationale=rationale_obj,
            error=error,
        )

        await store.append_node(run_id, node_trace)

    except ImportError:
        # Runtime not available (isolated agents tests) -- skip
        pass
    except Exception:
        # Never let trace capture break the pipeline
        pass

    # Emit OTEL span for the pipeline node (post-hoc, not wrapping)
    _emit_otel_node_span(
        run_id=run_id,
        node_name=node_name,
        status=status,
        time_ms=time_ms,
        quality_score=quality_score,
        error=error,
    )
