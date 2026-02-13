"""Agent-specific domain models (output types for Pydantic AI agents).

These extend the runtime domain entities with strongly-typed output schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RAGQuote(BaseModel):
    """A single RAG-sourced quote with provenance."""

    text: str = Field(..., description="Quoted text from the source document")
    doc_title: str = Field("", description="Source document title")
    section: str = Field("", description="Section within the source document")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Retrieval relevance score")


class QualityAssessment(BaseModel):
    """Output of the QualityGateAgent (ADR-050 tiered quality gate)."""

    score: int = Field(..., ge=0, le=100, description="Quality score 0-100")
    status: str = Field(..., description="accept | refine-if-budget | must-refine")
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    checklist: dict[str, bool] = Field(default_factory=dict)
    human_review_required: bool = False
    human_review_reasons: list[str] = Field(default_factory=list)

    # RAG-grounded quoting (Task #8)
    rag_quotes: list[RAGQuote] = Field(
        default_factory=list,
        description="1-3 RAG source quotes with provenance",
    )
    rag_confidence: str = Field(
        "low",
        description="Confidence label: high | medium | low based on retrieval score margin",
    )
    rag_sources_cited: bool = Field(
        False,
        description="Whether RAG sources were cited in the plan",
    )

    # Hard constraint results (Task #8)
    hard_constraints: dict[str, bool] = Field(
        default_factory=dict,
        description="Results of deterministic hard constraint checks",
    )


class ExecutorResult(BaseModel):
    """Output of the ExecutorAgent (replaces Claude Agent SDK, ADR-048)."""

    plan_id: str = ""
    plan_json: dict = Field(default_factory=dict)
    accessibility_report: dict = Field(default_factory=dict)
    exports: dict[str, str] = Field(default_factory=dict)
    score: int = 0
    human_review_required: bool = False
    summary_bullets: list[str] = Field(default_factory=list)
