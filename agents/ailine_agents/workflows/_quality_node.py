"""Quality gate / validation node for the plan generation LangGraph workflow.

Contains the make_validate_node factory, hard constraint application,
LLM-based quality gate scoring, and validation logging.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

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

from ..deps import AgentDeps
from ..model_selection.bridge import PydanticAIModelSelector
from ._node_shared import _check_timeout, _handle_node_failure
from ._retry import with_retry
from ._sse_helpers import get_emitter_and_writer, try_emit
from ._state import RunState
from ._trace_capture import capture_node_trace

__all__ = [
    "make_validate_node",
]


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

            cap_raw = state.get("class_accessibility_profile")
            class_profile = ClassAccessibilityProfile(**cap_raw) if cap_raw else None
            draft = state.get("draft") or {}
            validation = validate_draft_accessibility(draft, class_profile)

            # Hard constraints + RAG scoring
            rag_results = state.get("rag_results") or []
            validation = _apply_hard_constraints(
                validation, draft, class_profile, rag_results
            )

            det_score = validation["score"]
            final_score = det_score
            if 60 <= det_score <= 85 and deps.circuit_breaker.check():
                final_score = await _run_quality_gate_llm(
                    deps,
                    draft,
                    validation,
                    det_score,
                    run_id,
                    model_selector=model_selector,
                )
                validation["score"] = final_score

            validation["status"] = _score_to_status(final_score)

            duration_ms = (time.monotonic() - stage_start) * 1000
            _log_validate_success(
                run_id,
                final_score,
                validation["status"],
                duration_ms,
                emitter,
                writer,
                validation,
            )
            await capture_node_trace(
                run_id=run_id,
                node_name="validate",
                status="success",
                time_ms=duration_ms,
                inputs_summary={"draft_keys": list(draft.keys())[:10]},
                outputs_summary={
                    "score": final_score,
                    "quality_status": validation["status"],
                },
                quality_score=final_score,
            )

            return {"validation": validation, "quality_assessment": validation}  # type: ignore[typeddict-item,return-value]  # LangGraph partial state update

        except Exception as exc:
            await _handle_node_failure(
                exc,
                deps=deps,
                stage="validate",
                run_id=run_id,
                stage_start=stage_start,
                emitter=emitter,
                writer=writer,
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
    validation["rag_sources_cited"] = hard_constraints_dict.get(
        "rag_sources_cited", False
    )

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
    try_emit(
        emitter,
        writer,
        SSEEventType.QUALITY_SCORED,
        "validate",
        {
            "score": final_score,
            "status": status,
            "checklist": validation.get("checklist", {}),
        },
    )


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
            f"Evaluate this lesson plan. Deterministic score: {det_score}.\n"
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
                qg_prompt,
                deps=deps,
                **({"model": qg_model_override} if qg_model_override else {}),
            )

        qg_result = await with_retry(
            _run_qg,
            max_attempts=2,
            initial_delay=0.5,
            backoff_factor=2.0,
            operation_name="quality_gate.run",
            run_id=run_id,
        )

        llm_score = qg_result.output.score
        # Hysteresis: near decision thresholds (60, 80 +/- 5 points),
        # weight deterministic scoring higher to reduce LLM jitter.
        near_threshold = any(abs(det_score - t) <= 5 for t in (60, 80))
        if near_threshold:
            det_weight, llm_weight = 0.6, 0.4
        else:
            det_weight, llm_weight = 0.4, 0.6
        final_score = int(det_weight * det_score + llm_weight * llm_score)
        validation["llm_assessment"] = qg_result.output.model_dump()
        validation["score_breakdown"] = {
            "deterministic": det_score,
            "llm": llm_score,
            "weights": f"{det_weight}*det+{llm_weight}*llm",
            "near_threshold": near_threshold,
        }
        deps.circuit_breaker.record_success()
        log_event(
            "validate.llm_gate",
            run_id=run_id,
            det=det_score,
            llm=llm_score,
            final=final_score,
        )
        return final_score
    except Exception as llm_exc:
        deps.circuit_breaker.record_failure()
        log_event("validate.llm_gate_failed", run_id=run_id, error=str(llm_exc))
        return det_score
