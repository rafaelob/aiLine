"""RAG provenance domain entities (lightweight dataclass variant).

Complementary to rag_diagnostics.py (Pydantic-based), these dataclasses
provide a minimal, framework-free representation for provenance tracking
in contexts where Pydantic is not needed (e.g., agent-side code, tests).

RetrievalResult: single retrieved chunk with confidence classification.
RAGDiagnostics: complete diagnostics for a single RAG query.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class RetrievalResult:
    """A single retrieved chunk with provenance metadata."""

    chunk_id: str
    doc_title: str
    section: str
    score: float  # cosine similarity score
    confidence: Literal["high", "medium", "low"]
    text_preview: str  # first 200 chars of the chunk

    @staticmethod
    def classify_confidence(score: float) -> Literal["high", "medium", "low"]:
        """Classify a similarity score into a confidence tier.

        high >= 0.8, medium >= 0.6, low < 0.6
        """
        if score >= 0.8:
            return "high"
        if score >= 0.6:
            return "medium"
        return "low"


@dataclass
class RAGDiagnostics:
    """Complete diagnostics for a single RAG retrieval operation."""

    run_id: str
    query: str
    top_k: int
    filter_applied: dict[str, Any] = field(default_factory=dict)
    results: list[RetrievalResult] = field(default_factory=list)
    answerable: bool = False
    retrieval_time_ms: float = 0.0
    answerable_threshold: float = 0.6

    def compute_answerable(self) -> bool:
        """Determine if the query is answerable based on max retrieval score."""
        if not self.results:
            self.answerable = False
            return False
        max_score = max(r.score for r in self.results)
        self.answerable = max_score >= self.answerable_threshold
        return self.answerable

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "run_id": self.run_id,
            "query": self.query,
            "top_k": self.top_k,
            "filter_applied": self.filter_applied,
            "results": [
                {
                    "chunk_id": r.chunk_id,
                    "doc_title": r.doc_title,
                    "section": r.section,
                    "score": r.score,
                    "confidence": r.confidence,
                    "text_preview": r.text_preview,
                }
                for r in self.results
            ],
            "answerable": self.answerable,
            "retrieval_time_ms": self.retrieval_time_ms,
        }
