"""Plan generation workflow: PlannerAgent -> QualityGate -> Refine -> ExecutorAgent.

Pydantic AI agents called inside LangGraph nodes. SSE streaming preserved.
ADR-038: LangGraph custom stream_mode for SSE.
ADR-042: Explicit recursion_limit=25.
ADR-048: No Claude Agent SDK -- direct Pydantic AI agents.
ADR-050: Tiered quality gate (<60/60-79/>=80).

Resilience features:
- Retry with exponential backoff on transient LLM errors.
- Circuit breaker prevents cascading failures.
- Workflow timeout aborts gracefully after max_workflow_duration_seconds.
- Idempotency key prevents duplicate plan generations.
- Structured logging with run_id, stage, model, and duration.
"""

from __future__ import annotations

import json
import time
from typing import Any

import structlog
from ailine_runtime.accessibility.profiles import ClassAccessibilityProfile
from ailine_runtime.accessibility.validator import validate_draft_accessibility
from ailine_runtime.api.streaming.events import SSEEventType
from ailine_runtime.shared.observability import log_event, log_pipeline_stage
from langgraph.graph import END, StateGraph
from langgraph.types import RunnableConfig

from ..agents.executor import get_executor_agent
from ..agents.planner import get_planner_agent
from ..agents.quality_gate import get_quality_gate_agent
from ..deps import AgentDeps
from ..model_selection.bridge import PydanticAIModelSelector
from ..resilience import CircuitOpenError, IdempotencyGuard
from ._retry import with_retry
from ._sse_helpers import get_emitter_and_writer, try_emit
from ._state import RunState

log = structlog.get_logger(__name__)

DEFAULT_RECURSION_LIMIT = 25

# Module-level idempotency guard (single-process).
_idempotency_guard = IdempotencyGuard()


class WorkflowTimeoutError(Exception):
    """Raised when a workflow exceeds its maximum allowed duration."""


def _check_timeout(state: RunState, deps: AgentDeps, stage: str) -> None:
    """Check if the workflow has exceeded its time budget.

    Raises WorkflowTimeoutError if the elapsed time exceeds
    deps.max_workflow_duration_seconds.
    """
    started_at = state.get("started_at")
    if started_at is None:
        return
    elapsed = time.monotonic() - started_at
    if elapsed > deps.max_workflow_duration_seconds:
        run_id = state.get("run_id", "")
        log.error(
            "workflow.timeout",
            run_id=run_id,
            stage=stage,
            elapsed_seconds=round(elapsed, 1),
            limit_seconds=deps.max_workflow_duration_seconds,
        )
        raise WorkflowTimeoutError(
            f"Workflow timed out after {elapsed:.1f}s "
            f"(limit: {deps.max_workflow_duration_seconds}s) at stage '{stage}'"
        )


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
        stage_start = time.monotonic()

        # Set started_at on first entry (iteration 0)
        updates: dict[str, Any] = {}
        if state.get("started_at") is None:
            updates["started_at"] = time.monotonic()

        # Check timeout
        _check_timeout(state, deps, "planner")

        # Check circuit breaker
        if not deps.circuit_breaker.check():
            log_event("planner.circuit_open", run_id=run_id)
            try_emit(emitter, writer, SSEEventType.STAGE_FAILED, "planner", {
                "error": "Circuit breaker open -- LLM service unavailable",
            })
            raise CircuitOpenError("LLM circuit breaker is open")

        try:
            log_event("planner.start", run_id=run_id, stage="planner", refine_iter=refine_iter)

            if refine_iter > 0:
                try_emit(emitter, writer, SSEEventType.REFINEMENT_START, "planner", {"iteration": refine_iter})
            else:
                try_emit(emitter, writer, SSEEventType.STAGE_START, "planner")

            # Build prompt
            prompt = state["user_prompt"]

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
            model_name = "default"
            if model_selector:
                model_override = model_selector.select_model(tier="primary")
                model_name = str(model_override) if model_override else "default"

            # Run Pydantic AI agent with retry
            async def _run_planner():
                return await planner.run(
                    prompt,
                    deps=deps,
                    **({"model": model_override} if model_override else {}),
                )

            result = await with_retry(
                _run_planner,
                max_attempts=3,
                initial_delay=1.0,
                backoff_factor=2.0,
                operation_name="planner.run",
                run_id=run_id,
            )

            draft = result.output.model_dump()
            deps.circuit_breaker.record_success()

            duration_ms = (time.monotonic() - stage_start) * 1000
            log_event(
                "planner.complete",
                run_id=run_id,
                stage="planner",
                model=model_name,
                duration_ms=round(duration_ms, 2),
            )
            log_pipeline_stage(
                stage="planner",
                run_id=run_id,
                duration_ms=duration_ms,
                status="success",
                metadata={"model": model_name, "refine_iter": refine_iter},
            )

            if refine_iter > 0:
                try_emit(emitter, writer, SSEEventType.REFINEMENT_COMPLETE, "planner", {"iteration": refine_iter})
            else:
                try_emit(emitter, writer, SSEEventType.STAGE_COMPLETE, "planner")

            updates["draft"] = draft
            return updates

        except CircuitOpenError:
            raise
        except Exception as exc:
            deps.circuit_breaker.record_failure()
            duration_ms = (time.monotonic() - stage_start) * 1000
            log_event("planner.failed", run_id=run_id, error=str(exc), duration_ms=round(duration_ms, 2))
            log_pipeline_stage(
                stage="planner", run_id=run_id, duration_ms=duration_ms,
                status="failed", metadata={"error": str(exc)},
            )
            try_emit(emitter, writer, SSEEventType.STAGE_FAILED, "planner", {"error": str(exc)})
            raise

    async def validate_node(state: RunState, config: RunnableConfig) -> RunState:
        """Hybrid validation: deterministic first, LLM QualityGate for borderline (ADR-050)."""
        emitter, writer = get_emitter_and_writer(config)
        run_id = state.get("run_id", "")
        stage_start = time.monotonic()

        # Check timeout
        _check_timeout(state, deps, "validate")

        try:
            log_event("validate.start", run_id=run_id, stage="validate")
            try_emit(emitter, writer, SSEEventType.STAGE_START, "validate")

            class_profile = (
                ClassAccessibilityProfile(**state["class_accessibility_profile"])
                if state.get("class_accessibility_profile")
                else None
            )
            validation = validate_draft_accessibility(state.get("draft") or {}, class_profile)

            det_score = validation.get("score", 0)

            # Hybrid gate: if borderline (60-85), run QualityGateAgent
            final_score = det_score
            if 60 <= det_score <= 85 and deps.circuit_breaker.check():
                try:
                    qg_agent = get_quality_gate_agent()
                    draft_json = state.get("draft") or {}
                    qg_prompt = (
                        f"Avalie este plano de aula. Score deterministico: {det_score}.\n"
                        f"Draft: {json.dumps(draft_json, ensure_ascii=False)[:3000]}\n"
                        f"Checklist: {json.dumps(validation.get('checklist', {}), ensure_ascii=False)}\n"
                    )

                    async def _run_qg():
                        return await qg_agent.run(qg_prompt, deps=deps)

                    qg_result = await with_retry(
                        _run_qg,
                        max_attempts=2,
                        initial_delay=0.5,
                        backoff_factor=2.0,
                        operation_name="quality_gate.run",
                        run_id=run_id,
                    )

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
                    deps.circuit_breaker.record_success()
                    log_event(
                        "validate.llm_gate",
                        run_id=run_id,
                        det=det_score,
                        llm=llm_score,
                        final=final_score,
                    )
                except Exception as llm_exc:
                    # LLM gate failed -- fall back to deterministic only
                    deps.circuit_breaker.record_failure()
                    log_event("validate.llm_gate_failed", run_id=run_id, error=str(llm_exc))

            # Update status based on final score
            if final_score < 60:
                status = "must-refine"
            elif final_score < 80:
                status = "refine-if-budget"
            else:
                status = "accept"
            validation["status"] = status

            duration_ms = (time.monotonic() - stage_start) * 1000
            log_event(
                "validate.complete",
                run_id=run_id,
                stage="validate",
                score=final_score,
                status=status,
                duration_ms=round(duration_ms, 2),
            )
            log_pipeline_stage(
                stage="validate",
                run_id=run_id,
                duration_ms=duration_ms,
                status="success",
                metadata={"score": final_score, "quality_status": status},
            )
            try_emit(emitter, writer, SSEEventType.QUALITY_SCORED, "validate", {
                "score": final_score,
                "status": status,
                "checklist": validation.get("checklist", {}),
            })

            return {"validation": validation, "quality_assessment": validation}

        except Exception as exc:
            duration_ms = (time.monotonic() - stage_start) * 1000
            log_event("validate.failed", run_id=run_id, error=str(exc), duration_ms=round(duration_ms, 2))
            log_pipeline_stage(
                stage="validate", run_id=run_id, duration_ms=duration_ms,
                status="failed", metadata={"error": str(exc)},
            )
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
        stage_start = time.monotonic()

        # Check timeout
        _check_timeout(state, deps, "executor")

        # Check circuit breaker
        if not deps.circuit_breaker.check():
            log_event("executor.circuit_open", run_id=run_id)
            try_emit(emitter, writer, SSEEventType.STAGE_FAILED, "executor", {
                "error": "Circuit breaker open -- LLM service unavailable",
            })
            raise CircuitOpenError("LLM circuit breaker is open")

        try:
            log_event("executor.start", run_id=run_id, stage="executor")
            try_emit(emitter, writer, SSEEventType.STAGE_START, "executor")

            draft_json = state.get("draft") or {}
            prompt = _build_executor_prompt(
                draft_json,
                run_id,
                state.get("class_accessibility_profile"),
                deps.default_variants,
            )

            model_override = None
            model_name = "default"
            if model_selector:
                model_override = model_selector.select_model(tier="primary")
                model_name = str(model_override) if model_override else "default"

            async def _run_executor():
                return await executor.run(
                    prompt,
                    deps=deps,
                    **({"model": model_override} if model_override else {}),
                )

            result = await with_retry(
                _run_executor,
                max_attempts=3,
                initial_delay=1.0,
                backoff_factor=2.0,
                operation_name="executor.run",
                run_id=run_id,
            )

            deps.circuit_breaker.record_success()

            duration_ms = (time.monotonic() - stage_start) * 1000
            log_event(
                "executor.complete",
                run_id=run_id,
                stage="executor",
                model=model_name,
                duration_ms=round(duration_ms, 2),
            )
            log_pipeline_stage(
                stage="executor",
                run_id=run_id,
                duration_ms=duration_ms,
                status="success",
                metadata={"model": model_name, "plan_id": run_id},
            )
            try_emit(emitter, writer, SSEEventType.STAGE_COMPLETE, "executor", {"plan_id": run_id})

            return {"final": result.output.model_dump()}

        except CircuitOpenError:
            raise
        except Exception as exc:
            deps.circuit_breaker.record_failure()
            duration_ms = (time.monotonic() - stage_start) * 1000
            log_event("executor.failed", run_id=run_id, error=str(exc), duration_ms=round(duration_ms, 2))
            log_pipeline_stage(
                stage="executor", run_id=run_id, duration_ms=duration_ms,
                status="failed", metadata={"error": str(exc)},
            )
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


def get_idempotency_guard() -> IdempotencyGuard:
    """Access the module-level idempotency guard (for testing/reset)."""
    return _idempotency_guard


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
