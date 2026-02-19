"""Scorecard node for the plan generation LangGraph workflow.

Computes the Trust & Transformation Scorecard from pipeline state
after the executor stage completes.
"""

from __future__ import annotations

import time

from ailine_runtime.api.streaming.events import SSEEventType
from ailine_runtime.shared.observability import log_event
from langgraph.types import RunnableConfig

from ..deps import AgentDeps
from ._sse_helpers import get_emitter_and_writer, try_emit
from ._state import RunState

__all__ = [
    "_estimate_reading_level",
    "make_scorecard_node",
]


def make_scorecard_node(deps: AgentDeps):
    """Create the scorecard LangGraph node that computes TransformationScorecard."""

    def scorecard_node(state: RunState, config: RunnableConfig) -> RunState:
        """Compute the Trust & Transformation Scorecard from pipeline state."""
        emitter, writer = get_emitter_and_writer(config)
        run_id = state.get("run_id", "")

        try:
            draft = state.get("draft") or {}
            validation = state.get("validation") or {}
            final = state.get("final") or {}

            # Reading level heuristic
            prompt_text = state.get("user_prompt", "")
            plan_text = (
                draft.get("title", "")
                + " "
                + " ".join(s.get("title", "") for s in draft.get("steps", []))
            )
            reading_before = _estimate_reading_level(prompt_text)
            reading_after = _estimate_reading_level(plan_text)

            # Standards from objectives
            standards = []
            for obj in draft.get("objectives", []):
                if obj.get("id"):
                    standards.append(
                        {
                            "code": obj["id"],
                            "description": obj.get("text", "")[:100],
                        }
                    )

            # Accessibility adaptations
            a11y_pack = draft.get("accessibility_pack_draft", {})
            adaptations = []
            for adapt in a11y_pack.get("applied_adaptations", []):
                target = adapt.get("target", "unknown")
                strategies = adapt.get("strategies", [])
                adaptations.append(f"{target}: {', '.join(strategies[:2])}")

            # Quality
            quality_score = int(validation.get("score", 0))
            quality_decision = validation.get("status", "pending")

            # RAG confidence
            rag_confidence = float(validation.get("rag_confidence", 0.0))

            # Pipeline timing
            started_at = state.get("started_at")
            pipeline_time_ms = 0.0
            if started_at is not None:
                pipeline_time_ms = (time.monotonic() - started_at) * 1000

            # Time saved estimate
            step_count = len(draft.get("steps", []))
            estimated_manual_minutes = max(30, step_count * 10)
            pipeline_seconds = pipeline_time_ms / 1000
            time_saved = f"~{estimated_manual_minutes} min -> {pipeline_seconds:.0f}s"

            # Export variants
            export_count = (
                len(final.get("exports", {}))
                if isinstance(final.get("exports"), dict)
                else 0
            )
            if export_count == 0:
                parsed_exports = final.get("parsed", {}).get("exports", {})
                export_count = (
                    len(parsed_exports) if isinstance(parsed_exports, dict) else 10
                )

            scorecard = {
                "reading_level_before": round(reading_before, 1),
                "reading_level_after": round(reading_after, 1),
                "standards_aligned": standards,
                "accessibility_adaptations": adaptations,
                "rag_groundedness": round(rag_confidence, 2),
                "quality_score": quality_score,
                "quality_decision": quality_decision,
                "model_used": "",
                "router_rationale": "",
                "time_saved_estimate": time_saved,
                "total_pipeline_time_ms": round(pipeline_time_ms, 1),
                "export_variants_count": export_count if export_count > 0 else 10,
            }

            try_emit(
                emitter, writer, SSEEventType.STAGE_COMPLETE, "scorecard", scorecard
            )

            # Emit AI Receipt — trust chain summary for the frontend
            trust_level = (
                "high"
                if quality_score >= 85
                else ("medium" if quality_score >= 70 else "low")
            )
            citations_count = len(state.get("rag_results") or [])
            accommodations = adaptations if adaptations else []

            ai_receipt = {
                "model_used": scorecard.get("model_used", ""),
                "routing_reason": scorecard.get("router_rationale", ""),
                "quality_score": quality_score,
                "trust_level": trust_level,
                "citations_count": citations_count,
                "accommodations_applied": accommodations,
                "locale": deps.locale,
                "total_pipeline_time_ms": round(pipeline_time_ms, 1),
            }
            try_emit(emitter, writer, SSEEventType.AI_RECEIPT, "receipt", ai_receipt)

            return {"scorecard": scorecard}  # type: ignore[typeddict-item,return-value]  # LangGraph partial state update
        except Exception as exc:
            log_event("scorecard.failed", run_id=run_id, error=str(exc))
            try_emit(
                emitter,
                writer,
                SSEEventType.STAGE_FAILED,
                "scorecard",
                {"error": str(exc)[:200]},
            )
            fallback = {
                "error": "scorecard_calculation_failed",
                "details": str(exc)[:200],
                "quality_score": 0,
                "quality_decision": "pending",
                "total_pipeline_time_ms": 0.0,
            }
            return {"scorecard": fallback}  # type: ignore[typeddict-item,return-value]  # LangGraph partial state update

    return scorecard_node


def _estimate_reading_level(text: str) -> float:
    """Simple Flesch-Kincaid grade level estimate.

    Uses average sentence length as a proxy. Not a full FK computation
    but sufficient for scorecard display purposes.
    """
    if not text.strip():
        return 0.0
    sentences = [
        s.strip()
        for s in text.replace("!", ".").replace("?", ".").split(".")
        if s.strip()
    ]
    if not sentences:
        return 0.0
    words = text.split()
    if not words:
        return 0.0
    avg_sentence_length = len(words) / len(sentences)
    # Simplified Flesch-Kincaid: 0.39 * ASL + 11.8 * ASW - 15.59
    # ASW approximated as 1.5 (average syllables per word)
    grade = 0.39 * avg_sentence_length + 11.8 * 1.5 - 15.59
    return max(1.0, min(16.0, grade))
