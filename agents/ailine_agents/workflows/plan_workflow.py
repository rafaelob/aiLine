"""Plan generation workflow: PlannerAgent -> QualityGate -> Refine -> ExecutorAgent.

Pydantic AI agents called inside LangGraph nodes. SSE streaming preserved.
ADR-038: LangGraph custom stream_mode for SSE.
ADR-042: Explicit recursion_limit=25.
ADR-048: No Claude Agent SDK — direct Pydantic AI agents.
ADR-050: Tiered quality gate (<60/60-79/>=80).
"""

from __future__ import annotations

import json
from typing import Any

from ailine_runtime.accessibility.profiles import (
    AnonymousLearnerProfile,
    ClassAccessibilityProfile,
)
from ailine_runtime.accessibility.validator import validate_draft_accessibility
from ailine_runtime.api.streaming.events import SSEEventType
from ailine_runtime.shared.observability import log_event
from langgraph.graph import END, StateGraph
from langgraph.types import RunnableConfig

from ..agents.executor import get_executor_agent
from ..agents.planner import get_planner_agent
from ..agents.quality_gate import get_quality_gate_agent
from ..deps import AgentDeps
from ..model_selection.bridge import PydanticAIModelSelector
from ._sse_helpers import get_emitter_and_writer, try_emit
from ._state import RunState

DEFAULT_RECURSION_LIMIT = 25


def build_plan_workflow(
    deps: AgentDeps,
    *,
    model_selector: PydanticAIModelSelector | None = None,
) -> Any:
    """Build LangGraph plan workflow using Pydantic AI agents.

    Args:
        deps: AgentDeps (from AgentDepsFactory).
        model_selector: Optional SmartRouter -> Pydantic AI model bridge.

    Returns:
        Compiled LangGraph StateGraph.
    """
    graph = StateGraph(RunState)
    planner = get_planner_agent()
    executor = get_executor_agent()

    async def planner_node(state: RunState, config: RunnableConfig) -> RunState:
        emitter, writer = get_emitter_and_writer(config)
        run_id = state.get("run_id", "")
        refine_iter = int(state.get("refine_iter") or 0)

        try:
            log_event("planner.start", run_id=run_id)

            if refine_iter > 0:
                try_emit(emitter, writer, SSEEventType.REFINEMENT_START, "planner", {"iteration": refine_iter})
            else:
                try_emit(emitter, writer, SSEEventType.STAGE_START, "planner")

            # Build prompt
            prompt = state["user_prompt"]

            # Inject accessibility context
            (
                ClassAccessibilityProfile(**state["class_accessibility_profile"])
                if state.get("class_accessibility_profile")
                else None
            )
            if state.get("learner_profiles"):
                [AnonymousLearnerProfile(**lp) for lp in state["learner_profiles"]]

            # RAG context
            teacher_id = state.get("teacher_id")
            subject = state.get("subject")
            if teacher_id:
                prompt += (
                    f"\n\n## CONTEXTO DE MATERIAIS (RAG)\n"
                    f"- teacher_id: {teacher_id}\n"
                    f"- subject: {subject or ''}\n"
                    "Quando chamar rag_search, SEMPRE passe teacher_id.\n"
                )

            # Refinement feedback
            if refine_iter > 0:
                prev = state.get("quality_assessment") or state.get("validation") or {}
                prompt += _build_refinement_feedback(prev, refine_iter)

            # Select model
            model_override = None
            if model_selector:
                model_override = model_selector.select_model(tier="primary")

            # Run Pydantic AI agent
            result = await planner.run(
                prompt,
                deps=deps,
                **({"model": model_override} if model_override else {}),
            )

            draft = result.output.model_dump()
            log_event("planner.complete", run_id=run_id)

            if refine_iter > 0:
                try_emit(emitter, writer, SSEEventType.REFINEMENT_COMPLETE, "planner", {"iteration": refine_iter})
            else:
                try_emit(emitter, writer, SSEEventType.STAGE_COMPLETE, "planner")

            return {"draft": draft}

        except Exception as exc:
            log_event("planner.failed", run_id=run_id, error=str(exc))
            try_emit(emitter, writer, SSEEventType.STAGE_FAILED, "planner", {"error": str(exc)})
            raise

    async def validate_node(state: RunState, config: RunnableConfig) -> RunState:
        """Hybrid validation: deterministic first, LLM QualityGate for borderline (ADR-050)."""
        emitter, writer = get_emitter_and_writer(config)
        run_id = state.get("run_id", "")

        try:
            log_event("validate.start", run_id=run_id)
            try_emit(emitter, writer, SSEEventType.STAGE_START, "validate")

            class_profile = (
                ClassAccessibilityProfile(**state["class_accessibility_profile"])
                if state.get("class_accessibility_profile")
                else None
            )
            validation = validate_draft_accessibility(state.get("draft") or {}, class_profile)

            det_score = validation.get("score", 0)
            status = validation.get("status", "unknown")

            # Hybrid gate: if borderline (60-85), run QualityGateAgent for nuanced LLM assessment
            final_score = det_score
            if 60 <= det_score <= 85:
                try:
                    qg_agent = get_quality_gate_agent()
                    draft_json = state.get("draft") or {}
                    qg_prompt = (
                        f"Avalie este plano de aula. Score deterministico: {det_score}.\n"
                        f"Draft: {json.dumps(draft_json, ensure_ascii=False)[:3000]}\n"
                        f"Checklist: {json.dumps(validation.get('checklist', {}), ensure_ascii=False)}\n"
                    )
                    qg_result = await qg_agent.run(qg_prompt, deps=deps)
                    llm_score = qg_result.output.score
                    # Merge: 0.4 deterministic + 0.6 LLM
                    final_score = int(0.4 * det_score + 0.6 * llm_score)
                    validation["llm_assessment"] = qg_result.output.model_dump()
                    validation["score"] = final_score
                    validation["score_breakdown"] = {
                        "deterministic": det_score,
                        "llm": llm_score,
                        "weights": "0.4*det+0.6*llm",
                    }
                    log_event("validate.llm_gate", run_id=run_id, det=det_score, llm=llm_score, final=final_score)
                except Exception as llm_exc:
                    # LLM gate failed — fall back to deterministic only
                    log_event("validate.llm_gate_failed", run_id=run_id, error=str(llm_exc))

            # Update status based on final score
            if final_score < 60:
                status = "must-refine"
            elif final_score < 80:
                status = "refine-if-budget"
            else:
                status = "accept"
            validation["status"] = status

            log_event("validate.complete", run_id=run_id, score=final_score, status=status)
            try_emit(emitter, writer, SSEEventType.QUALITY_SCORED, "validate", {
                "score": final_score,
                "status": status,
                "checklist": validation.get("checklist", {}),
            })

            return {"validation": validation, "quality_assessment": validation}

        except Exception as exc:
            log_event("validate.failed", run_id=run_id, error=str(exc))
            try_emit(emitter, writer, SSEEventType.STAGE_FAILED, "validate", {"error": str(exc)})
            raise

    def decision_node(state: RunState, config: RunnableConfig) -> RunState:
        """Emit quality decision event."""
        emitter, writer = get_emitter_and_writer(config)

        try:
            v = state.get("validation") or {}
            score = int(v.get("score") or 0)
            refine_iter = int(state.get("refine_iter") or 0)

            if score < 60 and refine_iter < deps.max_refinement_iters:
                decision = "must-refine"
            elif score < 80 and refine_iter < deps.max_refinement_iters:
                decision = "refine-if-budget"
            else:
                decision = "accept"

            try_emit(emitter, writer, SSEEventType.QUALITY_DECISION, "validate", {
                "decision": decision,
                "score": score,
                "iteration": refine_iter,
            })

            return {}

        except Exception as exc:
            log_event("decision.failed", run_id=state.get("run_id", ""), error=str(exc))
            try_emit(emitter, writer, SSEEventType.STAGE_FAILED, "decision", {"error": str(exc)})
            raise

    def bump_refine_iter(state: RunState) -> RunState:
        new_iter = int(state.get("refine_iter") or 0) + 1
        log_event("refine.bump", run_id=state.get("run_id", ""), iteration=new_iter)
        return {"refine_iter": new_iter}

    async def executor_node(state: RunState, config: RunnableConfig) -> RunState:
        emitter, writer = get_emitter_and_writer(config)
        run_id = state.get("run_id", "")

        try:
            log_event("executor.start", run_id=run_id)
            try_emit(emitter, writer, SSEEventType.STAGE_START, "executor")

            draft_json = state.get("draft") or {}
            prompt = _build_executor_prompt(
                draft_json,
                run_id,
                state.get("class_accessibility_profile"),
                deps.default_variants,
            )

            model_override = None
            if model_selector:
                model_override = model_selector.select_model(tier="primary")

            result = await executor.run(
                prompt,
                deps=deps,
                **({"model": model_override} if model_override else {}),
            )

            log_event("executor.complete", run_id=run_id)
            try_emit(emitter, writer, SSEEventType.STAGE_COMPLETE, "executor", {"plan_id": run_id})

            return {"final": result.output.model_dump()}

        except Exception as exc:
            log_event("executor.failed", run_id=run_id, error=str(exc))
            try_emit(emitter, writer, SSEEventType.STAGE_FAILED, "executor", {"error": str(exc)})
            raise

    def should_execute(state: RunState) -> str:
        """Route based on tiered quality gate (ADR-050)."""
        v = state.get("validation") or {}
        score = int(v.get("score") or 0)
        refine_iter = int(state.get("refine_iter") or 0)

        if score < 60 and refine_iter < deps.max_refinement_iters:
            return "refine"
        if score < 80 and refine_iter < deps.max_refinement_iters:
            return "refine"
        return "execute"

    graph.add_node("planner", planner_node)
    graph.add_node("validate", validate_node)
    graph.add_node("decision", decision_node)
    graph.add_node("bump_refine", bump_refine_iter)
    graph.add_node("executor", executor_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "validate")
    graph.add_edge("validate", "decision")
    graph.add_conditional_edges(
        "decision",
        should_execute,
        {"refine": "bump_refine", "execute": "executor"},
    )
    graph.add_edge("bump_refine", "planner")
    graph.add_edge("executor", END)

    return graph.compile()


def _build_refinement_feedback(prev: dict[str, Any], refine_iter: int) -> str:
    """Build refinement feedback prompt from previous validation."""
    errors = prev.get("errors") or []
    warnings = prev.get("warnings") or []
    recs = prev.get("recommendations") or []
    score = prev.get("score")
    return (
        f"\n\n## FEEDBACK DO QUALITY GATE (refinement #{refine_iter})\n"
        f"- score_anterior: {score}\n"
        f"- erros: {errors}\n"
        f"- warnings: {warnings}\n"
        f"- recomendacoes: {recs}\n\n"
        "Ajuste o plano para enderecar os itens acima, mantendo o schema StudyPlanDraft."
    )


def _build_executor_prompt(
    draft_json: dict[str, Any],
    run_id: str,
    class_profile: dict[str, Any] | None,
    default_variants: str,
) -> str:
    """Build the executor agent prompt."""
    variants = [v.strip() for v in default_variants.split(",") if v.strip()]
    return (
        f"Finalize este plano draft.\n\n"
        f"run_id: {run_id}\n"
        f"variants: {json.dumps(variants, ensure_ascii=False)}\n"
        f"class_profile: {json.dumps(class_profile, ensure_ascii=False) if class_profile else 'null'}\n"
        f"draft_plan: {json.dumps(draft_json, ensure_ascii=False)}\n"
    )
