"""Observability Judge Dashboard API.

GET /observability/dashboard - System health + performance overview
GET /observability/standards-evidence/{run_id} - Standards alignment evidence for a run

Provides judges with real-time visibility into:
- LLM provider status + SmartRouter score breakdown
- Latency p50/p95
- Error rate + circuit breaker state
- SSE event counts by type
- Token usage/cost estimate
"""

from __future__ import annotations

import math
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException

from ...app.authz import require_authenticated
from ...shared.metrics import (
    circuit_breaker_state,
    http_requests_total,
    llm_call_duration,
    llm_calls_total,
)
from ...shared.observability_store import get_observability_store
from ...shared.trace_store import get_trace_store

logger = structlog.get_logger("ailine.api.observability")

router = APIRouter()


def _compute_percentiles(
    values: list[float], percentiles: list[float]
) -> dict[str, float]:
    """Compute percentile values from a sorted list."""
    if not values:
        return {f"p{int(p * 100)}": 0.0 for p in percentiles}
    s = sorted(values)
    n = len(s)
    result = {}
    for p in percentiles:
        idx = math.ceil(p * n) - 1
        idx = max(0, min(idx, n - 1))
        result[f"p{int(p * 100)}"] = round(s[idx], 2)
    return result


@router.get("/dashboard")
async def observability_dashboard(
    teacher_id: str = Depends(require_authenticated),
) -> dict[str, Any]:
    """System health and performance dashboard for judges.

    Returns current LLM provider info, SmartRouter breakdown,
    latency percentiles, error rates, circuit breaker state,
    SSE event counts, and token cost estimates.
    """
    obs_store = get_observability_store()

    # LLM metrics from counters
    llm_data = llm_calls_total.collect()
    total_llm_calls = sum(v for _, v in llm_data)
    error_calls = sum(v for labels, v in llm_data if labels.get("status") == "error")
    error_rate = round(error_calls / max(total_llm_calls, 1), 4)

    # Latency from histogram
    latency_data = llm_call_duration.collect()
    latency_values: list[float] = []
    for _, data in latency_data:
        count = data.get("_count", 0)
        if count > 0:
            avg = data.get("_sum", 0.0) / count
            latency_values.extend([avg] * count)

    latency_percentiles = _compute_percentiles(latency_values, [0.5, 0.95, 0.99])

    # HTTP metrics
    http_data = http_requests_total.collect()
    total_http_requests = sum(v for _, v in http_data)
    http_errors = sum(
        v for labels, v in http_data if labels.get("status", "").startswith("5")
    )

    # Circuit breaker state
    cb_data = circuit_breaker_state.collect()
    cb_transitions = {
        labels.get("transition", "unknown"): int(v) for labels, v in cb_data
    }

    # SSE event counts from observability store
    sse_counts = obs_store.get_sse_event_counts()

    # Token usage + cost estimate from observability store
    token_stats = obs_store.get_token_stats()

    # Recent SmartRouter score breakdown from trace store (tenant-scoped)
    trace_store = get_trace_store()
    recent_traces = await trace_store.list_recent(limit=10, teacher_id=teacher_id)
    router_breakdowns = []
    for trace in recent_traces:
        for node in trace.nodes:
            if node.route_rationale:
                router_breakdowns.append(
                    {
                        "run_id": trace.run_id,
                        "node": node.node,
                        "tier": node.route_rationale.tier,
                        "model": node.route_rationale.model_selected,
                        "scores": node.route_rationale.weighted_scores,
                    }
                )

    # Provider status
    provider_info = obs_store.get_provider_status()

    return {
        "llm": {
            "total_calls": int(total_llm_calls),
            "error_calls": int(error_calls),
            "error_rate": error_rate,
            "latency": latency_percentiles,
            "provider": provider_info,
        },
        "circuit_breaker": {
            "transitions": cb_transitions,
            "state": obs_store.get_circuit_breaker_state(),
        },
        "http": {
            "total_requests": int(total_http_requests),
            "server_errors": int(http_errors),
        },
        "sse": {
            "event_counts": sse_counts,
        },
        "tokens": token_stats,
        "smart_router": {
            "recent_decisions": router_breakdowns[:10],
        },
        "pipeline": {
            "recent_runs": len(recent_traces),
            "completed": sum(1 for t in recent_traces if t.status == "completed"),
            "failed": sum(1 for t in recent_traces if t.status == "failed"),
        },
    }


@router.get("/standards-evidence/{run_id}")
async def standards_evidence(
    run_id: str, teacher_id: str = Depends(require_authenticated)
) -> dict[str, Any]:
    """Standards alignment evidence for a specific plan run.

    Returns curriculum standard tags (BNCC/CCSS/NGSS), Bloom level,
    and a 1-2 sentence explainer for why the plan aligns.
    Also includes export-as-teacher-handout option.
    Scoped to the authenticated teacher (tenant isolation).
    """
    trace_store = get_trace_store()
    trace = await trace_store.get(run_id, teacher_id=teacher_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail=f"No trace found for run_id={run_id}",
        )

    # Extract standards evidence from the trace nodes
    draft_data: dict[str, Any] = {}
    for node in trace.nodes:
        if node.node == "planner" and node.outputs_summary:
            draft_data = node.outputs_summary
        if node.node == "executor" and node.outputs_summary:
            draft_data.update(node.outputs_summary)

    # Build standards alignment evidence
    obs_store = get_observability_store()
    evidence = obs_store.get_standards_evidence(run_id)

    return {
        "run_id": run_id,
        "status": trace.status,
        "final_score": trace.final_score,
        "standards": evidence.get("standards", []),
        "bloom_level": evidence.get("bloom_level"),
        "alignment_explanation": evidence.get("alignment_explanation", ""),
        "handout_available": True,
        "handout_url": f"/observability/standards-evidence/{run_id}/handout",
    }


@router.get("/standards-evidence/{run_id}/handout")
async def standards_handout(
    run_id: str, teacher_id: str = Depends(require_authenticated)
) -> dict[str, Any]:
    """Export standards alignment as teacher handout format.

    Returns structured data suitable for rendering as a printable
    teacher handout with standards tags, alignment rationale,
    and quality score.
    Scoped to the authenticated teacher (tenant isolation).
    """
    trace_store = get_trace_store()
    trace = await trace_store.get(run_id, teacher_id=teacher_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail=f"No trace found for run_id={run_id}",
        )

    obs_store = get_observability_store()
    evidence = obs_store.get_standards_evidence(run_id)

    quality_data: dict[str, Any] = {}
    for node in trace.nodes:
        if node.node == "validate" and node.quality_score is not None:
            quality_data = {
                "score": node.quality_score,
                "status": node.outputs_summary.get("quality_status", ""),
            }

    return {
        "run_id": run_id,
        "type": "teacher_handout",
        "title": f"Standards Alignment Report - {run_id}",
        "standards": evidence.get("standards", []),
        "bloom_level": evidence.get("bloom_level"),
        "alignment_explanation": evidence.get("alignment_explanation", ""),
        "quality": quality_data,
        "pipeline_nodes": [
            {
                "node": n.node,
                "status": n.status,
                "time_ms": n.time_ms,
            }
            for n in trace.nodes
        ],
        "total_time_ms": trace.total_time_ms,
        "generated_by": "AiLine Adaptive Inclusive Learning Platform",
    }
