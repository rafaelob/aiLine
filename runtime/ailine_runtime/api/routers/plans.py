"""Plans API router — plan generation pipeline."""

from __future__ import annotations

from typing import Any

from ailine_agents import AgentDepsFactory
from ailine_agents.workflows.plan_workflow import build_plan_workflow
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter()


class PlanGenerateIn(BaseModel):
    run_id: str = Field(..., description="Run ID for observability.")
    user_prompt: str
    teacher_id: str | None = Field(None, description="Optional: teacher ID (needed for RAG).")
    subject: str | None = Field(None, description="Optional: subject (RAG filter).")
    class_accessibility_profile: dict[str, Any] | None = None
    learner_profiles: list[dict[str, Any]] | None = None


@router.post("/generate")
async def plans_generate(body: PlanGenerateIn, request: Request):
    container = request.app.state.container
    settings = request.app.state.settings

    deps = AgentDepsFactory.from_container(
        container,
        teacher_id=body.teacher_id or "",
        run_id=body.run_id,
        subject=body.subject or "",
        default_variants=getattr(settings, "default_variants", "standard_html"),
        max_refinement_iters=getattr(settings, "max_refinement_iters", 2),
    )
    workflow = build_plan_workflow(deps)

    init_state = {
        "run_id": body.run_id,
        "user_prompt": body.user_prompt,
        "teacher_id": body.teacher_id,
        "subject": body.subject,
        "class_accessibility_profile": body.class_accessibility_profile,
        "learner_profiles": body.learner_profiles,
        "refine_iter": 0,
    }

    final_state = await workflow.ainvoke(init_state)
    return final_state
