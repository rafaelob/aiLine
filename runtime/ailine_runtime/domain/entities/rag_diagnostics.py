"""RAG diagnostics domain entities.

Models for RAG retrieval diagnostics: provenance metadata, answerability
checks, and per-run diagnostic reports.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RAGChunkProvenance(BaseModel):
    """Provenance metadata for a single retrieved chunk."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    doc_title: str = Field("", description="Source document title")
    doc_id: str = Field("", description="Source document ID")
    page: int | None = Field(None, description="Page number if available")
    section: str = Field("", description="Section/heading within the document")
    retrieval_score: float = Field(0.0, ge=0.0, le=1.0, description="Cosine similarity score")
    text_preview: str = Field("", description="First 200 chars of chunk text")


class AnswerabilityCheck(BaseModel):
    """Result of checking whether retrieval results can answer the query."""

    answerable: bool = Field(True, description="Whether the query is answerable from retrieved chunks")
    confidence: str = Field("high", description="high | medium | low")
    top_score: float = Field(0.0, description="Highest retrieval score")
    score_threshold: float = Field(0.7, description="Minimum score for answerability")
    reason: str = Field("", description="Human-readable explanation")


class RAGDiagnostics(BaseModel):
    """Complete RAG diagnostics report for a single query/run."""

    run_id: str = Field(..., description="Pipeline run ID or query ID")
    teacher_id: str = Field("", description="Owning teacher for tenant isolation")
    query: str = Field("", description="Original query text")
    chunks: list[RAGChunkProvenance] = Field(
        default_factory=list,
        description="Retrieved chunks with provenance",
    )
    top_k_requested: int = Field(5, description="Number of candidates requested")
    top_k_returned: int = Field(0, description="Number of candidates returned before threshold")
    filters_applied: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata filters applied to the search",
    )
    answerability: AnswerabilityCheck = Field(
        default_factory=AnswerabilityCheck,
        description="Answerability assessment",
    )
    selection_rationale: str = Field(
        "",
        description="Why these documents were selected (threshold, score gap, etc.)",
    )


def check_answerability(
    scores: list[float],
    threshold: float = 0.7,
) -> AnswerabilityCheck:
    """Check if retrieval scores indicate the query is answerable.

    Rules:
    - No results -> not answerable (low confidence)
    - Top score < threshold -> not answerable (low confidence)
    - Top score >= threshold but < threshold+0.1 -> answerable but medium confidence
    - Top score >= threshold+0.1 -> answerable with high confidence
    """
    if not scores:
        return AnswerabilityCheck(
            answerable=False,
            confidence="low",
            top_score=0.0,
            score_threshold=threshold,
            reason="No retrieval results found",
        )

    top = max(scores)

    if top < threshold:
        return AnswerabilityCheck(
            answerable=False,
            confidence="low",
            top_score=round(top, 4),
            score_threshold=threshold,
            reason=f"Top retrieval score ({top:.3f}) below threshold ({threshold})",
        )

    confidence = "high" if top >= threshold + 0.1 else "medium"
    return AnswerabilityCheck(
        answerable=True,
        confidence=confidence,
        top_score=round(top, 4),
        score_threshold=threshold,
        reason=f"Top retrieval score ({top:.3f}) meets threshold ({threshold})",
    )


def build_diagnostics(
    *,
    run_id: str,
    query: str,
    results: list[dict[str, Any]],
    k_requested: int = 5,
    filters: dict[str, Any] | None = None,
    threshold: float = 0.7,
) -> RAGDiagnostics:
    """Build a complete RAG diagnostics report from search results.

    Each result dict should have: id/chunk_id, score/similarity,
    text/content, and optional metadata (title, page, section, doc_id).
    """
    chunks: list[RAGChunkProvenance] = []
    scores: list[float] = []

    for r in results:
        score = float(r.get("score") or r.get("similarity") or r.get("relevance_score") or 0.0)
        scores.append(score)

        text = r.get("text") or r.get("content") or r.get("chunk") or ""
        preview = text[:200] if len(text) > 200 else text

        metadata = r.get("metadata") or {}
        chunks.append(RAGChunkProvenance(
            chunk_id=str(r.get("id") or r.get("chunk_id") or ""),
            doc_title=str(r.get("title") or metadata.get("title") or r.get("doc_title") or ""),
            doc_id=str(r.get("doc_id") or metadata.get("doc_id") or ""),
            page=r.get("page") or metadata.get("page"),
            section=str(r.get("section") or metadata.get("section") or r.get("heading") or ""),
            retrieval_score=round(score, 4),
            text_preview=preview,
        ))

    answerability = check_answerability(scores, threshold=threshold)

    # Build selection rationale
    if not scores:
        rationale = "No documents retrieved"
    else:
        above = sum(1 for s in scores if s >= threshold)
        rationale = (
            f"{above}/{len(scores)} chunks above threshold ({threshold}). "
            f"Score range: [{min(scores):.3f}, {max(scores):.3f}]."
        )

    return RAGDiagnostics(
        run_id=run_id,
        query=query,
        chunks=chunks,
        top_k_requested=k_requested,
        top_k_returned=len(results),
        filters_applied=filters or {},
        answerability=answerability,
        selection_rationale=rationale,
    )
