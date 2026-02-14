"""Plans API router — plan generation pipeline."""

from __future__ import annotations

from typing import Any

from ailine_agents import AgentDepsFactory
from ailine_agents.workflows.plan_workflow import build_plan_workflow
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...app.authz import require_authenticated
from ...shared.sanitize import sanitize_prompt

router = APIRouter()

# Fields safe to expose to the client from the LangGraph RunState.
# Internal workflow fields (refine_iter, started_at, idempotency_key, etc.)
# are explicitly excluded to prevent information leakage.
_SAFE_RESPONSE_FIELDS = frozenset({
    "run_id",
    "draft",
    "quality_assessment",
    "quality_decision",
    "validation",
    "final",
})


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
