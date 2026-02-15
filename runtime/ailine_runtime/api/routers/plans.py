"""Plans API router — plan generation pipeline."""

from __future__ import annotations

from typing import Any

from ailine_agents import AgentDepsFactory
from ailine_agents.workflows.plan_workflow import build_plan_workflow
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...app.authz import require_authenticated
from ...domain.entities.plan import ReviewStatus
from ...shared.review_store import get_review_store
from ...shared.sanitize import sanitize_prompt
from ...shared.trace_store import get_trace_store

router = APIRouter()

# Fields safe to expose to the client from the LangGraph RunState.
# Internal workflow fields (refine_iter, started_at, idempotency_key, etc.)
# are explicitly excluded to prevent information leakage.
_SAFE_RESPONSE_FIELDS = frozenset(
    {
        "run_id",
        "draft",
        "quality_assessment",
        "quality_decision",
        "validation",
        "final",
        "scorecard",
    }
)


class PlanGenerateIn(BaseModel):
    run_id: str = Field(..., description="Run ID for observability.")
    user_prompt: str
    teacher_id: str | None = Field(None, description="Optional: teacher ID (needed for RAG).")
    subject: str | None = Field(None, description="Optional: subject (RAG filter).")
    class_accessibility_profile: dict[str, Any] | None = None
    learner_profiles: list[dict[str, Any]] | None = None


def _resolve_teacher_id() -> str:
    """Resolve teacher_id from JWT context (mandatory).

    Raises 401 if no authenticated teacher context is available.
    """
    return require_authenticated()


def _filter_state(state: dict[str, Any]) -> dict[str, Any]:
    """Filter raw LangGraph state to only expose safe fields to the client."""
    return {k: v for k, v in state.items() if k in _SAFE_RESPONSE_FIELDS}


@router.post("/generate", response_model=dict[str, Any])
async def plans_generate(body: PlanGenerateIn, request: Request):
    container = request.app.state.container
    settings = request.app.state.settings

    # --- Input sanitization ---
    user_prompt = sanitize_prompt(body.user_prompt)
    if not user_prompt:
        raise HTTPException(status_code=422, detail="user_prompt must not be empty after sanitization")

    teacher_id = _resolve_teacher_id()

    deps = AgentDepsFactory.from_container(
        container,
        teacher_id=teacher_id,
        run_id=body.run_id,
        subject=body.subject or "",
        default_variants=getattr(settings, "default_variants", "standard_html"),
        max_refinement_iters=getattr(settings, "max_refinement_iters", 2),
    )
    workflow = build_plan_workflow(deps)

    init_state = {
        "run_id": body.run_id,
        "user_prompt": user_prompt,
        "teacher_id": teacher_id,
        "subject": body.subject,
        "class_accessibility_profile": body.class_accessibility_profile,
        "learner_profiles": body.learner_profiles,
        "refine_iter": 0,
    }

    final_state = await workflow.ainvoke(init_state)
    return _filter_state(final_state)


# ---------------------------------------------------------------------------
# HITL Plan Review endpoints
# ---------------------------------------------------------------------------


class PlanReviewIn(BaseModel):
    status: str = Field(..., description="approved|rejected|needs_revision")
    notes: str = Field("", max_length=2000)


@router.post("/{plan_id}/review")
async def plan_review(plan_id: str, body: PlanReviewIn):
    """Submit a teacher review for a plan (HITL approval gate)."""
    teacher_id = _resolve_teacher_id()
    store = get_review_store()

    existing = store.get_review(plan_id)
    if not existing:
        store.create_review(plan_id, teacher_id)

    try:
        status = ReviewStatus(body.status)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=f"Invalid status: {body.status}") from err

    review = store.update_review(plan_id, status, body.notes)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review.model_dump()


@router.get("/{plan_id}/review")
async def plan_review_get(plan_id: str):
    """Get the review status for a plan."""
    _resolve_teacher_id()
    store = get_review_store()
    review = store.get_review(plan_id)
    if not review:
        raise HTTPException(status_code=404, detail="No review found for this plan")
    return review.model_dump()


@router.get("/pending-review", response_model=list[dict[str, Any]])
async def plans_pending_review():
    """List all plans pending teacher review."""
    teacher_id = _resolve_teacher_id()
    store = get_review_store()
    reviews = store.list_pending(teacher_id)
    return [r.model_dump() for r in reviews]


# ---------------------------------------------------------------------------
# Transformation Scorecard endpoint
# ---------------------------------------------------------------------------


@router.get("/{run_id}/scorecard")
async def plans_scorecard(run_id: str):
    """Get the transformation scorecard for a completed plan run."""
    _resolve_teacher_id()

    trace_store = get_trace_store()
    trace = await trace_store.get(run_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Run not found")

    if not trace.scorecard:
        raise HTTPException(status_code=404, detail="Scorecard not yet available")

    return trace.scorecard
