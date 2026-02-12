"""Agent-specific domain models (output types for Pydantic AI agents).

These extend the runtime domain entities with strongly-typed output schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


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


class ExecutorResult(BaseModel):
    """Output of the ExecutorAgent (replaces Claude Agent SDK, ADR-048)."""

    plan_id: str = ""
    plan_json: dict = Field(default_factory=dict)
    accessibility_report: dict = Field(default_factory=dict)
    exports: dict[str, str] = Field(default_factory=dict)
    score: int = 0
    human_review_required: bool = False
    summary_bullets: list[str] = Field(default_factory=list)
