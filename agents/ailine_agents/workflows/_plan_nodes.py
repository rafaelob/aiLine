"""Extracted LangGraph node functions for the plan workflow.

Contains the planner_node, validate_node, and executor_node
implementations. Extracted from plan_workflow.py to keep the
main module focused on graph construction and routing logic.
"""

from __future__ import annotations

import json
import time
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from ailine_runtime.accessibility.hard_constraints import (
    compute_rag_confidence,
    extract_rag_quotes,
    run_hard_constraints,
)
from ailine_runtime.accessibility.profiles import ClassAccessibilityProfile
from ailine_runtime.accessibility.validator import validate_draft_accessibility
from ailine_runtime.api.streaming.events import SSEEvent, SSEEventEmitter, SSEEventType
from ailine_runtime.shared.observability import log_event, log_pipeline_stage
from langgraph.types import RunnableConfig
from pydantic_ai import Agent

from ..deps import AgentDeps
from ..model_selection.bridge import PydanticAIModelSelector
from ..resilience import CircuitOpenError
from ._retry import with_retry
from ._sse_helpers import get_emitter_and_writer, try_emit
from ._state import RunState
from ._trace_capture import build_route_rationale, capture_node_trace

log = structlog.get_logger(__name__)


class WorkflowTimeoutError(Exception):
    """Raised when a workflow exceeds its maximum allowed duration."""


def _check_timeout(state: RunState, deps: AgentDeps, stage: str) -> None:
    """Check if the workflow has exceeded its time budget."""
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


def _select_model(
    model_selector: PydanticAIModelSelector | None,
) -> tuple[Any, str]:
    """Select model from SmartRouter or return defaults."""
    if model_selector:
        model_override = model_selector.select_model(tier="primary")
        model_name = str(model_override) if model_override else "default"
        return model_override, model_name
    return None, "default"


# ---------------------------------------------------------------------------
# Shared error-handling helper for LLM agent nodes
# ---------------------------------------------------------------------------


async def _handle_node_failure(
    exc: Exception,
    *,
    deps: AgentDeps,
    stage: str,
    run_id: str,
    stage_start: float,
    emitter: SSEEventEmitter | None,
    writer: Callable[[SSEEvent], None] | None,
) -> None:
    """Record failure metrics, emit SSE, and capture trace for a failed node."""
    deps.circuit_breaker.record_failure()
    duration_ms = (time.monotonic() - stage_start) * 1000
    log_event(f"{stage}.failed", run_id=run_id, error=str(exc), duration_ms=round(duration_ms, 2))
    log_pipeline_stage(
        stage=stage, run_id=run_id, duration_ms=duration_ms,
        status="failed", metadata={"error": str(exc)},
    )
    try_emit(emitter, writer, SSEEventType.STAGE_FAILED, stage, {"error": str(exc)})
    await capture_node_trace(
        run_id=run_id, node_name=stage, status="failed",
        time_ms=duration_ms, error=str(exc),
    )


async def _run_agent_with_resilience(
    *,
    agent_fn: Callable[[], Awaitable[Any]],
    deps: AgentDeps,
    stage: str,
    run_id: str,
    stage_start: float,
    emitter: SSEEventEmitter | None,
    writer: Callable[[SSEEvent], None] | None,
    max_attempts: int = 3,
) -> Any:
    """Run an agent callable with retry and circuit breaker recording.

    Returns the result on success. Raises on failure after recording metrics.
    """
    if not deps.circuit_breaker.check():
        log_event(f"{stage}.circuit_open", run_id=run_id)
        try_emit(emitter, writer, SSEEventType.STAGE_FAILED, stage, {
            "error": "Circuit breaker open -- LLM service unavailable",
        })
        raise CircuitOpenError("LLM circuit breaker is open")

    try:
        result = await with_retry(
            agent_fn,
            max_attempts=max_attempts,
            initial_delay=1.0,
            backoff_factor=2.0,
            operation_name=f"{stage}.run",
            run_id=run_id,
        )
        deps.circuit_breaker.record_success()
        return result
    except CircuitOpenError:
        raise
    except Exception as exc:
        await _handle_node_failure(
            exc, deps=deps, stage=stage, run_id=run_id,
            stage_start=stage_start, emitter=emitter, writer=writer,
        )
        raise


def _log_node_success(
    *,
    stage: str,
    run_id: str,
    model_name: str,
    duration_ms: float,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Log success event and pipeline stage for a completed node."""
    log_event(
        f"{stage}.complete", run_id=run_id, stage=stage,
        model=model_name, duration_ms=round(duration_ms, 2),
    )
    log_pipeline_stage(
        stage=stage, run_id=run_id, duration_ms=duration_ms,
        status="success", metadata={"model": model_name, **(metadata or {})},
    )


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
        f"\n\n## FEEDBACK DO QUALITY GATE (refinement #{refine_iter})\n"
        f"- score_anterior: {score}\n"
        f"- erros: {errors}\n"
        f"- warnings: {warnings}\n"
        f"- recomendacoes: {recs}\n\n"
        "Ajuste o plano para enderecar os itens acima, mantendo o schema StudyPlanDraft."
    )


def build_executor_prompt(
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


# ---------------------------------------------------------------------------
# Node factory functions
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

        log_event("planner.start", run_id=run_id, stage="planner", refine_iter=refine_iter)

        model_override, model_name = _select_model(model_selector)
        rationale = build_route_rationale(
            task_type="planner", model_name=model_name, model_selector=model_selector,
        )

        # SSE start event (refinement vs initial)
        if refine_iter > 0:
            try_emit(emitter, writer, SSEEventType.REFINEMENT_START, "planner", {
                "iteration": refine_iter, "route_rationale": rationale,
            })
        else:
            try_emit(emitter, writer, SSEEventType.STAGE_START, "planner", {
                "route_rationale": rationale,
            })

        # Build prompt
        prompt = _build_planner_prompt(state, refine_iter)

        async def _run():
            return await planner.run(
                prompt, deps=deps,
                **({"model": model_override} if model_override else {}),
            )

        result = await _run_agent_with_resilience(
            agent_fn=_run, deps=deps, stage="planner", run_id=run_id,
            stage_start=stage_start, emitter=emitter, writer=writer,
        )

        draft = result.output.model_dump()
        duration_ms = (time.monotonic() - stage_start) * 1000

        _log_node_success(
            stage="planner", run_id=run_id, model_name=model_name,
            duration_ms=duration_ms, metadata={"refine_iter": refine_iter},
        )

        if refine_iter > 0:
            try_emit(emitter, writer, SSEEventType.REFINEMENT_COMPLETE, "planner", {"iteration": refine_iter})
        else:
            try_emit(emitter, writer, SSEEventType.STAGE_COMPLETE, "planner")

        await capture_node_trace(
            run_id=run_id, node_name="planner", status="success",
            time_ms=duration_ms,
            inputs_summary={"prompt_length": len(prompt), "refine_iter": refine_iter},
            outputs_summary={"draft_keys": list(draft.keys())[:10]},
            route_rationale=rationale,
        )

        updates["draft"] = draft
        return updates

    return planner_node


def _build_planner_prompt(state: RunState, refine_iter: int) -> str:
    """Build the planner agent prompt with RAG context and refinement feedback."""
    prompt = state["user_prompt"]

    teacher_id = state.get("teacher_id")
    subject = state.get("subject")
    if teacher_id:
        prompt += (
            f"\n\n## CONTEXTO DE MATERIAIS (RAG)\n"
            f"- teacher_id: {teacher_id}\n"
            f"- subject: {subject or ''}\n"
            "Quando chamar rag_search, SEMPRE passe teacher_id.\n"
        )

    if refine_iter > 0:
        prev = state.get("quality_assessment") or state.get("validation") or {}
        prompt += build_refinement_feedback(prev, refine_iter)

    return prompt


def make_validate_node(
    deps: AgentDeps,
    model_selector: PydanticAIModelSelector | None = None,
):
    """Create the validate LangGraph node function."""

    async def validate_node(state: RunState, config: RunnableConfig) -> RunState:
        """Hybrid validation: deterministic first, LLM QualityGate for borderline (ADR-050)."""
        emitter, writer = get_emitter_and_writer(config)
        run_id = state.get("run_id", "")
        stage_start = time.monotonic()

        _check_timeout(state, deps, "validate")

        try:
            log_event("validate.start", run_id=run_id, stage="validate")
            try_emit(emitter, writer, SSEEventType.STAGE_START, "validate")

            class_profile = (
                ClassAccessibilityProfile(**state["class_accessibility_profile"])
                if state.get("class_accessibility_profile")
                else None
            )
            draft = state.get("draft") or {}
            validation = validate_draft_accessibility(draft, class_profile)

            # Hard constraints + RAG scoring
            rag_results = state.get("rag_results") or []
            validation = _apply_hard_constraints(validation, draft, class_profile, rag_results)

            det_score = validation["score"]
            final_score = det_score
            if 60 <= det_score <= 85 and deps.circuit_breaker.check():
                final_score = await _run_quality_gate_llm(
                    deps, draft, validation, det_score, run_id,
                    model_selector=model_selector,
                )
                validation["score"] = final_score

            validation["status"] = _score_to_status(final_score)

            duration_ms = (time.monotonic() - stage_start) * 1000
            _log_validate_success(
                run_id, final_score, validation["status"], duration_ms,
                emitter, writer, validation,
            )
            await capture_node_trace(
                run_id=run_id, node_name="validate", status="success",
                time_ms=duration_ms,
                inputs_summary={"draft_keys": list(draft.keys())[:10]},
                outputs_summary={"score": final_score, "quality_status": validation["status"]},
                quality_score=final_score,
            )

            return {"validation": validation, "quality_assessment": validation}

        except Exception as exc:
            await _handle_node_failure(
                exc, deps=deps, stage="validate", run_id=run_id,
                stage_start=stage_start, emitter=emitter, writer=writer,
            )
            raise

    return validate_node


def _apply_hard_constraints(
    validation: dict[str, Any],
    draft: dict[str, Any],
    class_profile: ClassAccessibilityProfile | None,
    rag_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Apply hard constraints and RAG scoring to validation result."""
    hard_results = run_hard_constraints(draft, class_profile, rag_results)
    hard_constraints_dict = {r.name: r.passed for r in hard_results}
    hard_failures = [r for r in hard_results if not r.passed]

    validation["hard_constraints"] = hard_constraints_dict
    validation["hard_constraint_details"] = [r.model_dump() for r in hard_results]

    hard_penalty = len(hard_failures) * 5
    for failure in hard_failures:
        if failure.reason not in validation.get("warnings", []):
            validation.setdefault("warnings", []).append(failure.reason)

    rag_confidence = compute_rag_confidence(rag_results)
    rag_quotes = extract_rag_quotes(rag_results)
    validation["rag_confidence"] = rag_confidence
    validation["rag_quotes"] = rag_quotes
    validation["rag_sources_cited"] = hard_constraints_dict.get("rag_sources_cited", False)

    validation["score"] = max(0, validation.get("score", 0) - hard_penalty)
    return validation


def _score_to_status(score: int) -> str:
    """Convert quality score to status string (ADR-050)."""
    if score < 60:
        return "must-refine"
    if score < 80:
        return "refine-if-budget"
    return "accept"


def _log_validate_success(
    run_id: str,
    final_score: int,
    status: str,
    duration_ms: float,
    emitter: SSEEventEmitter | None,
    writer: Callable[[SSEEvent], None] | None,
    validation: dict[str, Any],
) -> None:
    """Log and emit events for successful validation."""
    log_event(
        "validate.complete", run_id=run_id, stage="validate",
        score=final_score, status=status, duration_ms=round(duration_ms, 2),
    )
    log_pipeline_stage(
        stage="validate", run_id=run_id, duration_ms=duration_ms,
        status="success",
        metadata={"score": final_score, "quality_status": status},
    )
    try_emit(emitter, writer, SSEEventType.QUALITY_SCORED, "validate", {
        "score": final_score, "status": status,
        "checklist": validation.get("checklist", {}),
    })


async def _run_quality_gate_llm(
    deps: AgentDeps,
    draft: dict[str, Any],
    validation: dict[str, Any],
    det_score: int,
    run_id: str,
    *,
    model_selector: PydanticAIModelSelector | None = None,
) -> int:
    """Run the LLM-based QualityGate for borderline scores."""
    from ..agents.quality_gate import get_quality_gate_agent

    try:
        qg_agent = get_quality_gate_agent()
        qg_prompt = (
            f"Avalie este plano de aula. Score deterministico: {det_score}.\n"
            f"Draft: {json.dumps(draft, ensure_ascii=False)[:3000]}\n"
            f"Checklist: {json.dumps(validation.get('checklist', {}), ensure_ascii=False)}\n"
            f"Hard constraints: {json.dumps(validation.get('hard_constraints', {}), ensure_ascii=False)}\n"
            f"RAG confidence: {validation.get('rag_confidence')}\n"
            f"RAG quotes: {json.dumps(validation.get('rag_quotes', []), ensure_ascii=False)[:500]}\n"
        )

        qg_model_override = None
        if model_selector:
            qg_model_override = model_selector.select_model(tier="middle")

        async def _run_qg():
            return await qg_agent.run(
                qg_prompt, deps=deps,
                **({"model": qg_model_override} if qg_model_override else {}),
            )

        qg_result = await with_retry(
            _run_qg, max_attempts=2, initial_delay=0.5,
            backoff_factor=2.0, operation_name="quality_gate.run", run_id=run_id,
        )

        llm_score = qg_result.output.score
        final_score = int(0.4 * det_score + 0.6 * llm_score)
        validation["llm_assessment"] = qg_result.output.model_dump()
        validation["score_breakdown"] = {
            "deterministic": det_score, "llm": llm_score, "weights": "0.4*det+0.6*llm",
        }
        deps.circuit_breaker.record_success()
        log_event("validate.llm_gate", run_id=run_id, det=det_score, llm=llm_score, final=final_score)
        return final_score
    except Exception as llm_exc:
        deps.circuit_breaker.record_failure()
        log_event("validate.llm_gate_failed", run_id=run_id, error=str(llm_exc))
        return det_score


def make_executor_node(
    executor: Agent[AgentDeps, Any],
    deps: AgentDeps,
    model_selector: PydanticAIModelSelector | None,
):
    """Create the executor LangGraph node function."""

    async def executor_node(state: RunState, config: RunnableConfig) -> RunState:
        emitter, writer = get_emitter_and_writer(config)
        run_id = state.get("run_id", "")
        stage_start = time.monotonic()

        _check_timeout(state, deps, "executor")

        log_event("executor.start", run_id=run_id, stage="executor")

        model_override, model_name = _select_model(model_selector)
        exec_rationale = build_route_rationale(
            task_type="executor", model_name=model_name, model_selector=model_selector,
        )
        try_emit(emitter, writer, SSEEventType.STAGE_START, "executor", {
            "route_rationale": exec_rationale,
        })

        draft_json = state.get("draft") or {}
        prompt = build_executor_prompt(
            draft_json, run_id,
            state.get("class_accessibility_profile"),
            deps.default_variants,
        )

        async def _run():
            return await executor.run(
                prompt, deps=deps,
                **({"model": model_override} if model_override else {}),
            )

        result = await _run_agent_with_resilience(
            agent_fn=_run, deps=deps, stage="executor", run_id=run_id,
            stage_start=stage_start, emitter=emitter, writer=writer,
        )

        duration_ms = (time.monotonic() - stage_start) * 1000
        _log_node_success(
            stage="executor", run_id=run_id, model_name=model_name,
            duration_ms=duration_ms, metadata={"plan_id": run_id},
        )
        try_emit(emitter, writer, SSEEventType.STAGE_COMPLETE, "executor", {"plan_id": run_id})

        await capture_node_trace(
            run_id=run_id, node_name="executor", status="success",
            time_ms=duration_ms,
            inputs_summary={"draft_keys": list(draft_json.keys())[:10]},
            outputs_summary={"plan_id": run_id},
            route_rationale=exec_rationale,
        )

        return {"final": result.output.model_dump()}

    return executor_node
