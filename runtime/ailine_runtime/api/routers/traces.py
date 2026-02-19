"""Trace viewer API for agent pipeline observability.

GET /traces/{run_id}   - Full trace for a specific run
GET /traces/recent     - List recent run traces (summary)

Serves the Agent Trace Viewer frontend panel, letting judges
inspect the Planner -> QualityGate -> Refine -> Executor pipeline
with per-node timing, tool calls, quality scores, and routing rationale.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from ...app.authz import require_authenticated
from ...shared.trace_store import get_trace_store

logger = structlog.get_logger("ailine.api.traces")

router = APIRouter()


@router.get("/recent")
async def list_recent_traces(
    limit: int = Query(20, ge=1, le=50),
    teacher_id: str = Depends(require_authenticated),
) -> list[dict[str, Any]]:
    """List recent pipeline traces (lightweight summary).

    Returns basic info: run_id, status, total_time_ms, node count,
    final_score, model_used, refinement_count.
    Scoped to the authenticated teacher (tenant isolation).
    """
    store = get_trace_store()
    traces = await store.list_recent(limit=min(limit, 50), teacher_id=teacher_id)
    return [
        {
            "run_id": t.run_id,
            "status": t.status,
            "total_time_ms": round(t.total_time_ms, 1),
            "node_count": len(t.nodes),
            "final_score": t.final_score,
            "model_used": t.model_used,
            "refinement_count": t.refinement_count,
        }
        for t in traces
    ]


@router.get("/{run_id}")
async def get_trace(
    run_id: str, teacher_id: str = Depends(require_authenticated)
) -> dict[str, Any]:
    """Get the full execution trace for a pipeline run.

    Returns the complete RunTrace with per-node detail:
    inputs/outputs summary, time_ms, tool_calls, quality_score,
    and route_rationale for nodes that select a model.
    Scoped to the authenticated teacher (tenant isolation).
    """
    store = get_trace_store()
    trace = await store.get(run_id, teacher_id=teacher_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trace not found for run_id={run_id}",
        )
    return trace.model_dump()
