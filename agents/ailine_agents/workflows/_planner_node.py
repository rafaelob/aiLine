"""Planner node for the plan generation LangGraph workflow.

Contains the make_planner_node factory, prompt building helpers,
and refinement feedback formatting.
"""

from __future__ import annotations

import time
from typing import Any

from ailine_runtime.api.streaming.events import SSEEventType
from ailine_runtime.shared.observability import log_event
from langgraph.types import RunnableConfig
from pydantic_ai import Agent

from ..deps import AgentDeps
from ..model_selection.bridge import PydanticAIModelSelector
from ._node_shared import (
    _check_timeout,
    _log_node_success,
    _run_agent_with_resilience,
    _select_model,
)
from ._sse_helpers import get_emitter_and_writer, try_emit
from ._state import RunState
from ._trace_capture import build_route_rationale, capture_node_trace

__all__ = [
    "build_refinement_feedback",
    "make_planner_node",
]


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------


def build_refinement_feedback(prev: dict[str, Any], refine_iter: int) -> str:
    """Build refinement feedback prompt from previous validation."""
    errors = prev.get("errors") or []
    warnings = prev.get("warnings") or []
    recs = prev.get("recommendations") or []
    score = prev.get("score")
    return (
        f"\n\n## QUALITY GATE FEEDBACK (refinement #{refine_iter})\n"
        f"- previous_score: {score}\n"
        f"- errors: {errors}\n"
        f"- warnings: {warnings}\n"
        f"- recommendations: {recs}\n\n"
        "Adjust the plan to address the items above while keeping the StudyPlanDraft schema."
    )


def _build_planner_prompt(state: RunState, refine_iter: int) -> str:
    """Build the planner agent prompt with skills, RAG context, and refinement feedback."""
    prompt = state["user_prompt"]

    # Inject activated skills fragment (from skills_node, F-177)
    skill_fragment = state.get("skill_prompt_fragment") or ""
    if skill_fragment:
        prompt += f"\n\n{skill_fragment}"

    teacher_id = state.get("teacher_id")
    subject = state.get("subject")
    if teacher_id:
        prompt += (
            f"\n\n## MATERIALS CONTEXT (RAG)\n"
            f"- teacher_id: {teacher_id}\n"
            f"- subject: {subject or ''}\n"
            "When calling rag_search, ALWAYS pass teacher_id.\n"
        )

    if refine_iter > 0:
        prev = state.get("quality_assessment") or state.get("validation") or {}
        prompt += build_refinement_feedback(prev, refine_iter)

    return prompt


# ---------------------------------------------------------------------------
# Node factory
# ---------------------------------------------------------------------------


def make_planner_node(
    planner: Agent[AgentDeps, Any],
    deps: AgentDeps,
    model_selector: PydanticAIModelSelector | None,
):
    """Create the planner LangGraph node function."""

    async def planner_node(state: RunState, config: RunnableConfig) -> RunState:
        emitter, writer = get_emitter_and_writer(config)
        run_id = state.get("run_id", "")
        refine_iter = int(state.get("refine_iter") or 0)
        stage_start = time.monotonic()

        updates: dict[str, Any] = {}
        if state.get("started_at") is None:
            updates["started_at"] = time.monotonic()

        _check_timeout(state, deps, "planner")

        log_event(
            "planner.start", run_id=run_id, stage="planner", refine_iter=refine_iter
        )

        model_override, model_name = _select_model(model_selector)
        rationale = build_route_rationale(
            task_type="planner",
            model_name=model_name,
            model_selector=model_selector,
        )

        # SSE start event (refinement vs initial)
        if refine_iter > 0:
            try_emit(
                emitter,
                writer,
                SSEEventType.REFINEMENT_START,
                "planner",
                {
                    "iteration": refine_iter,
                    "route_rationale": rationale,
                },
            )
        else:
            try_emit(
                emitter,
                writer,
                SSEEventType.STAGE_START,
                "planner",
                {
                    "route_rationale": rationale,
                },
            )

        # Build prompt
        prompt = _build_planner_prompt(state, refine_iter)

        async def _run():
            return await planner.run(
                prompt,
                deps=deps,
                **({"model": model_override} if model_override else {}),
            )

        result = await _run_agent_with_resilience(
            agent_fn=_run,
            deps=deps,
            stage="planner",
            run_id=run_id,
            stage_start=stage_start,
            emitter=emitter,
            writer=writer,
        )

        draft = result.output.model_dump()
        duration_ms = (time.monotonic() - stage_start) * 1000

        _log_node_success(
            stage="planner",
            run_id=run_id,
            model_name=model_name,
            duration_ms=duration_ms,
            metadata={"refine_iter": refine_iter},
        )

        if refine_iter > 0:
            try_emit(
                emitter,
                writer,
                SSEEventType.REFINEMENT_COMPLETE,
                "planner",
                {"iteration": refine_iter},
            )
        else:
            try_emit(emitter, writer, SSEEventType.STAGE_COMPLETE, "planner")

        await capture_node_trace(
            run_id=run_id,
            node_name="planner",
            status="success",
            time_ms=duration_ms,
            inputs_summary={"prompt_length": len(prompt), "refine_iter": refine_iter},
            outputs_summary={"draft_keys": list(draft.keys())[:10]},
            route_rationale=rationale,
        )

        updates["draft"] = draft
        return updates  # type: ignore[typeddict-item,return-value]  # LangGraph partial state update

    return planner_node
