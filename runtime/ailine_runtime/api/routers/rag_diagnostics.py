"""RAG diagnostics API for retrieval observability.

GET /rag/diagnostics/{run_id}   - Full diagnostics for a specific run
GET /rag/diagnostics/recent     - List recent RAG diagnostics (summary)

Provides retrieval diagnostics: top-k scores, filters applied,
chunk provenance, and answerability assessment.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException

from ...shared.rag_diagnostics_store import get_rag_diagnostics_store

logger = structlog.get_logger("ailine.api.rag_diagnostics")

router = APIRouter()


@router.get("/diagnostics/recent")
async def list_recent_diagnostics(limit: int = 20) -> list[dict[str, Any]]:
    """List recent RAG diagnostics (lightweight summary).

    Returns: run_id, query preview, chunk count, top score,
    answerability status, filters applied.
    """
    store = get_rag_diagnostics_store()
    diagnostics = await store.list_recent(limit=min(limit, 50))
    return [
        {
            "run_id": d.run_id,
            "query_preview": d.query[:100] if d.query else "",
            "chunks_returned": len(d.chunks),
            "top_score": d.answerability.top_score,
            "answerable": d.answerability.answerable,
            "confidence": d.answerability.confidence,
            "filters": d.filters_applied,
        }
        for d in diagnostics
    ]


@router.get("/diagnostics/{run_id}")
async def get_diagnostics(run_id: str) -> dict[str, Any]:
    """Get full RAG diagnostics for a specific run.

    Returns chunk provenance (chunk IDs, document titles, page/section
    references, retrieval scores), filters applied, answerability check,
    and selection rationale.
    """
    store = get_rag_diagnostics_store()
    diag = await store.get(run_id)
    if diag is None:
        raise HTTPException(
            status_code=404,
            detail=f"RAG diagnostics not found for run_id={run_id}",
        )
    return diag.model_dump()
