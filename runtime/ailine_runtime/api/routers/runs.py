"""Runs API — RESTful resource model for plan pipeline runs (F-237).

GET /runs           — list runs (paginated, filterable by status)
GET /runs/{run_id}  — full run detail with trace data
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ...app.authz import require_authenticated
from ...shared.trace_store import get_trace_store

router = APIRouter()


@router.get("")
async def list_runs(
    teacher_id: str = Depends(require_authenticated),
    status: str | None = Query(None, pattern=r"^(running|completed|failed)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List plan pipeline runs for the authenticated teacher.

    Supports filtering by ``status`` (running, completed, failed)
    and cursor-based pagination via ``limit`` + ``offset``.
    """
    store = get_trace_store()
    # Fetch more than needed to apply status filter after
    all_traces = await store.list_recent(limit=500, teacher_id=teacher_id)

    if status:
        all_traces = [t for t in all_traces if t.status == status]

    total = len(all_traces)
    page = all_traces[offset : offset + limit]

    return {
        "items": [
            {
                "run_id": t.run_id,
                "status": t.status,
                "created_at": t.created_at,
                "user_prompt": t.user_prompt[:200] if t.user_prompt else "",
                "subject": t.subject,
                "total_time_ms": round(t.total_time_ms, 1),
                "final_score": t.final_score,
                "model_used": t.model_used,
                "node_count": len(t.nodes),
                "refinement_count": t.refinement_count,
            }
            for t in page
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{run_id}")
async def get_run(
    run_id: str,
    teacher_id: str = Depends(require_authenticated),
) -> dict[str, Any]:
    """Get full detail for a single pipeline run.

    Returns the complete RunTrace with per-node execution data,
    scorecard, and metadata. Scoped to the authenticated teacher.
    """
    store = get_trace_store()
    trace = await store.get(run_id, teacher_id=teacher_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    return trace.model_dump()
