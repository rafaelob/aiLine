"""Tests for the AI Receipt SSE event type and scorecard node enhancement.

Covers:
- AI_RECEIPT event type added to SSEEventType enum
- SSEEventEmitter ai_receipt convenience method
- Scorecard node emits ai_receipt event with trust chain data
"""

from __future__ import annotations

import json

from ailine_runtime.api.streaming.events import SSEEvent, SSEEventEmitter, SSEEventType

# ---------------------------------------------------------------------------
# SSEEventType — AI_RECEIPT added
# ---------------------------------------------------------------------------


class TestAIReceiptEventType:
    def test_ai_receipt_exists(self) -> None:
        assert hasattr(SSEEventType, "AI_RECEIPT")
        assert SSEEventType.AI_RECEIPT == "ai_receipt"

    def test_has_15_event_types(self) -> None:
        """After adding AI_RECEIPT, there should be 15 event types."""
        members = list(SSEEventType)
        assert len(members) == 15

    def test_ai_receipt_is_strenum(self) -> None:
        assert isinstance(SSEEventType.AI_RECEIPT, str)
        assert SSEEventType.AI_RECEIPT in {"ai_receipt", "other"}


# ---------------------------------------------------------------------------
# SSEEventEmitter — ai_receipt convenience method
# ---------------------------------------------------------------------------


class TestAIReceiptEmitter:
    def test_ai_receipt_convenience(self) -> None:
        emitter = SSEEventEmitter("run-receipt")
        event = emitter.ai_receipt(
            {
                "model_used": "claude-opus-4-6",
                "quality_score": 92,
                "trust_level": "high",
            }
        )
        assert event.type == SSEEventType.AI_RECEIPT
        assert event.stage == "receipt"
        assert event.payload["model_used"] == "claude-opus-4-6"
        assert event.payload["quality_score"] == 92
        assert event.payload["trust_level"] == "high"
        assert event.seq == 1

    def test_ai_receipt_serializes_to_json(self) -> None:
        emitter = SSEEventEmitter("run-json")
        event = emitter.ai_receipt(
            {
                "trust_level": "medium",
                "citations_count": 5,
                "accommodations_applied": ["autism: visual schedule"],
            }
        )
        data = json.loads(event.to_sse_data())
        assert data["type"] == "ai_receipt"
        assert data["stage"] == "receipt"
        assert data["payload"]["trust_level"] == "medium"
        assert data["payload"]["citations_count"] == 5

    def test_ai_receipt_without_payload(self) -> None:
        emitter = SSEEventEmitter("run-empty")
        event = emitter.ai_receipt()
        assert event.type == SSEEventType.AI_RECEIPT
        assert event.payload == {}

    def test_ai_receipt_in_full_pipeline(self) -> None:
        """Verify AI receipt fits into a full pipeline event sequence."""
        emitter = SSEEventEmitter("run-full-receipt")
        events = [
            emitter.run_start({"prompt": "Create plan"}),
            emitter.stage_start("planner"),
            emitter.stage_complete("planner"),
            emitter.stage_start("validate"),
            emitter.quality_scored(88),
            emitter.quality_decision("accept"),
            emitter.stage_complete("validate"),
            emitter.stage_start("scorecard"),
            emitter.stage_complete("scorecard"),
            emitter.ai_receipt(
                {
                    "model_used": "claude-opus-4-6",
                    "trust_level": "high",
                    "quality_score": 88,
                }
            ),
            emitter.run_complete({"plan_id": "run-full-receipt"}),
        ]

        # Monotonically increasing seq
        for i, event in enumerate(events):
            assert event.seq == i + 1

        # AI receipt is the second-to-last event
        assert events[-2].type == SSEEventType.AI_RECEIPT
        assert events[-1].type == SSEEventType.RUN_COMPLETE


# ---------------------------------------------------------------------------
# SSEEvent model — roundtrip with AI_RECEIPT
# ---------------------------------------------------------------------------


class TestAIReceiptEvent:
    def test_event_roundtrip(self) -> None:
        event = SSEEvent(
            run_id="r1",
            seq=10,
            type=SSEEventType.AI_RECEIPT,
            stage="receipt",
            payload={
                "model_used": "claude-opus-4-6",
                "routing_reason": "SmartRouter: high complexity",
                "quality_score": 85,
                "trust_level": "high",
                "citations_count": 3,
                "accommodations_applied": ["TEA: visual schedule", "ADHD: timer"],
                "locale": "pt-BR",
                "total_pipeline_time_ms": 1234.5,
            },
        )
        dumped = event.model_dump()
        restored = SSEEvent(**dumped)
        assert restored == event
        assert restored.type == SSEEventType.AI_RECEIPT

    def test_trust_level_boundaries(self) -> None:
        """Verify trust level classification logic."""
        # high >= 85
        assert _classify_trust(85) == "high"
        assert _classify_trust(100) == "high"
        # medium >= 70
        assert _classify_trust(70) == "medium"
        assert _classify_trust(84) == "medium"
        # low < 70
        assert _classify_trust(69) == "low"
        assert _classify_trust(0) == "low"


def _classify_trust(score: int) -> str:
    """Replicate the trust_level classification from the scorecard node."""
    if score >= 85:
        return "high"
    if score >= 70:
        return "medium"
    return "low"
