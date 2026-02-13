"""RAG provenance utilities: confidence scoring and quote extraction.

Extracted from hard_constraints.py for single-responsibility. These
functions are used by QualityGate to attach provenance metadata to
quality assessments.
"""

from __future__ import annotations

from typing import Any


def compute_rag_confidence(
    rag_results: list[dict[str, Any]] | None,
) -> str:
    """Compute confidence label based on retrieval score margin.

    Returns "high", "medium", or "low" based on the top result's
    relevance score and the gap between top and second result.
    """
    if not rag_results:
        return "low"

    scores = []
    for r in rag_results:
        score = r.get("score") or r.get("relevance_score") or r.get("similarity") or 0.0
        scores.append(float(score))

    if not scores:
        return "low"

    scores.sort(reverse=True)
    top = scores[0]

    if top >= 0.85:
        return "high"
    if top >= 0.65:
        # Check margin between top and second
        if len(scores) > 1:
            margin = top - scores[1]
            if margin >= 0.15:
                return "high"
        return "medium"
    return "low"


def extract_rag_quotes(
    rag_results: list[dict[str, Any]] | None,
    max_quotes: int = 3,
) -> list[dict[str, Any]]:
    """Extract top RAG quotes with provenance for inclusion in QualityAssessment.

    Returns list of dicts matching RAGQuote schema.
    """
    if not rag_results:
        return []

    quotes = []
    for r in rag_results[:max_quotes]:
        text = r.get("content") or r.get("text") or r.get("chunk") or ""
        if not text:
            continue

        # Truncate long quotes
        if len(text) > 300:
            text = text[:297] + "..."

        quotes.append({
            "text": text,
            "doc_title": r.get("title") or r.get("doc_title") or r.get("filename") or "",
            "section": r.get("section") or r.get("heading") or "",
            "relevance_score": float(
                r.get("score") or r.get("relevance_score") or r.get("similarity") or 0.0
            ),
        })

    return quotes
