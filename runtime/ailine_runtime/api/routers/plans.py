"""Plans API router — plan generation pipeline."""

from __future__ import annotations

from typing import Any

from ailine_agents import AgentDepsFactory
from ailine_agents.workflows.plan_workflow import build_plan_workflow
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...shared.sanitize import sanitize_prompt, validate_teacher_id
from ...shared.tenant import try_get_current_teacher_id

router = APIRouter()


class PlanGenerateIn(BaseModel):
    run_id: str = Field(..., description="Run ID for observability.")
    user_prompt: str
    teacher_id: str | None = Field(None, description="Optional: teacher ID (needed for RAG).")
    subject: str | None = Field(None, description="Optional: subject (RAG filter).")
    class_accessibility_profile: dict[str, Any] | None = None
    learner_profiles: list[dict[str, Any]] | None = None


def _resolve_teacher_id(body_teacher_id: str | None) -> str:
    """Resolve teacher_id: middleware context takes precedence over request body.

    Returns an empty string if neither source provides a value.
    """
    # Middleware-injected tenant context takes precedence
    ctx_teacher_id = try_get_current_teacher_id()
    if ctx_teacher_id:
        return ctx_teacher_id

    # Fall back to request body (backward compatibility)
    if body_teacher_id:
        try:
            return validate_teacher_id(body_teacher_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ""


@router.post("/generate")
async def plans_generate(body: PlanGenerateIn, request: Request):
    container = request.app.state.container
    settings = request.app.state.settings

    # --- Input sanitization ---
    user_prompt = sanitize_prompt(body.user_prompt)
    if not user_prompt:
        raise HTTPException(status_code=422, detail="user_prompt must not be empty after sanitization")

    teacher_id = _resolve_teacher_id(body.teacher_id)

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
        "teacher_id": teacher_id if teacher_id else body.teacher_id,
        "subject": body.subject,
        "class_accessibility_profile": body.class_accessibility_profile,
        "learner_profiles": body.learner_profiles,
        "refine_iter": 0,
    }

    final_state = await workflow.ainvoke(init_state)
    return final_state
