"""Tests for the typed SSE event system.

Covers:
- SSEEvent serialization and deserialization
- SSEEventEmitter sequence numbering
- All 14 event types
- Convenience methods
- Edge cases (empty payload, long payloads, unicode)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from ailine_runtime.api.streaming.events import SSEEvent, SSEEventEmitter, SSEEventType

# ---------------------------------------------------------------------------
# SSEEventType enum
# ---------------------------------------------------------------------------


class TestSSEEventType:
    """Verify all 14 event types are defined with correct values."""

    def test_has_15_event_types(self) -> None:
        members = list(SSEEventType)
        assert len(members) == 15

    def test_run_lifecycle_events(self) -> None:
        assert SSEEventType.RUN_START == "run.started"
        assert SSEEventType.RUN_COMPLETE == "run.completed"
        assert SSEEventType.RUN_FAILED == "run.failed"

    def test_stage_lifecycle_events(self) -> None:
        assert SSEEventType.STAGE_START == "stage.started"
        assert SSEEventType.STAGE_PROGRESS == "stage.progress"
        assert SSEEventType.STAGE_COMPLETE == "stage.completed"
        assert SSEEventType.STAGE_FAILED == "stage.failed"

    def test_quality_events(self) -> None:
        assert SSEEventType.QUALITY_SCORED == "quality.scored"
        assert SSEEventType.QUALITY_DECISION == "quality.decision"

    def test_refinement_events(self) -> None:
        assert SSEEventType.REFINEMENT_START == "refinement.started"
        assert SSEEventType.REFINEMENT_COMPLETE == "refinement.completed"

    def test_tool_events(self) -> None:
        assert SSEEventType.TOOL_START == "tool.started"
        assert SSEEventType.TOOL_COMPLETE == "tool.completed"

    def test_heartbeat_event(self) -> None:
        assert SSEEventType.HEARTBEAT == "heartbeat"

    def test_strenum_membership(self) -> None:
        """Ensure StrEnum allows string comparison."""
        assert SSEEventType.RUN_START == "run.started"
        assert SSEEventType.RUN_START == "run.started"
        assert SSEEventType.RUN_START in {"run.started", "other"}


# ---------------------------------------------------------------------------
# SSEEvent model
# ---------------------------------------------------------------------------


class TestSSEEvent:
    """Verify SSEEvent serialization and field defaults."""

    def test_create_event_with_all_fields(self) -> None:
        event = SSEEvent(
            run_id="test-123",
            seq=1,
            type=SSEEventType.RUN_START,
            stage="init",
            payload={"key": "value"},
        )
        assert event.run_id == "test-123"
        assert event.seq == 1
        assert event.type == SSEEventType.RUN_START
        assert event.stage == "init"
        assert event.payload == {"key": "value"}

    def test_timestamp_default(self) -> None:
        before = datetime.now(UTC)
        event = SSEEvent(
            run_id="r1",
            seq=1,
            type=SSEEventType.HEARTBEAT,
            stage="heartbeat",
        )
        after = datetime.now(UTC)
        # Timestamp should be a valid ISO string between before and after
        ts = datetime.fromisoformat(event.ts)
        assert before <= ts <= after

    def test_payload_default_empty(self) -> None:
        event = SSEEvent(
            run_id="r1",
            seq=1,
            type=SSEEventType.STAGE_START,
            stage="planner",
        )
        assert event.payload == {}

    def test_to_sse_data_returns_valid_json(self) -> None:
        event = SSEEvent(
            run_id="r1",
            seq=5,
            type=SSEEventType.QUALITY_SCORED,
            stage="validate",
            payload={"score": 85},
        )
        data = event.to_sse_data()
        parsed = json.loads(data)
        assert parsed["run_id"] == "r1"
        assert parsed["seq"] == 5
        assert parsed["type"] == "quality.scored"
        assert parsed["stage"] == "validate"
        assert parsed["payload"]["score"] == 85
        assert "ts" in parsed

    def test_to_sse_data_unicode_preserved(self) -> None:
        """Ensure ensure_ascii=False preserves unicode characters."""
        event = SSEEvent(
            run_id="r1",
            seq=1,
            type=SSEEventType.STAGE_PROGRESS,
            stage="planner",
            payload={"message": "Gerando plano de aula inclusivo para alunos com TEA"},
        )
        data = event.to_sse_data()
        assert "inclusivo" in data
        assert "\\u" not in data  # No escaped unicode

    def test_model_dump_roundtrip(self) -> None:
        event = SSEEvent(
            run_id="r1",
            seq=3,
            type=SSEEventType.TOOL_COMPLETE,
            stage="executor",
            payload={"tool": "save_plan", "result": {"plan_id": "abc"}},
        )
        dumped = event.model_dump()
        restored = SSEEvent(**dumped)
        assert restored == event

    def test_event_with_nested_payload(self) -> None:
        payload = {
            "checklist": {
                "has_steps": True,
                "has_instructions": True,
            },
            "scores": [85, 90, 78],
            "metadata": {"nested": {"deep": True}},
        }
        event = SSEEvent(
            run_id="r1",
            seq=1,
            type=SSEEventType.QUALITY_SCORED,
            stage="validate",
            payload=payload,
        )
        data = json.loads(event.to_sse_data())
        assert data["payload"]["checklist"]["has_steps"] is True
        assert data["payload"]["scores"] == [85, 90, 78]
        assert data["payload"]["metadata"]["nested"]["deep"] is True


# ---------------------------------------------------------------------------
# SSEEventEmitter
# ---------------------------------------------------------------------------


class TestSSEEventEmitter:
    """Verify emitter sequence management and convenience methods."""

    def test_initial_state(self) -> None:
        emitter = SSEEventEmitter("run-001")
        assert emitter.run_id == "run-001"
        assert emitter.seq == 0

    def test_emit_increments_seq(self) -> None:
        emitter = SSEEventEmitter("run-001")
        e1 = emitter.emit(SSEEventType.RUN_START, "init")
        e2 = emitter.emit(SSEEventType.STAGE_START, "planner")
        e3 = emitter.emit(SSEEventType.STAGE_COMPLETE, "planner")

        assert e1.seq == 1
        assert e2.seq == 2
        assert e3.seq == 3
        assert emitter.seq == 3

    def test_emit_carries_run_id(self) -> None:
        emitter = SSEEventEmitter("my-run")
        event = emitter.emit(SSEEventType.HEARTBEAT, "heartbeat")
        assert event.run_id == "my-run"

    def test_emit_with_payload(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.emit(SSEEventType.STAGE_PROGRESS, "planner", {"percent": 50})
        assert event.payload == {"percent": 50}

    def test_emit_without_payload(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.emit(SSEEventType.STAGE_START, "planner")
        assert event.payload == {}

    def test_run_start_convenience(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.run_start({"prompt": "hello"})
        assert event.type == SSEEventType.RUN_START
        assert event.stage == "init"
        assert event.payload == {"prompt": "hello"}

    def test_run_complete_convenience(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.run_complete({"plan_id": "abc"})
        assert event.type == SSEEventType.RUN_COMPLETE
        assert event.stage == "done"
        assert event.payload["plan_id"] == "abc"

    def test_run_failed_convenience(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.run_failed("timeout", stage="executor")
        assert event.type == SSEEventType.RUN_FAILED
        assert event.stage == "executor"
        assert event.payload["error"] == "timeout"

    def test_stage_start_convenience(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.stage_start("planner", {"model": "claude"})
        assert event.type == SSEEventType.STAGE_START
        assert event.stage == "planner"
        assert event.payload["model"] == "claude"

    def test_stage_progress_convenience(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.stage_progress("planner", {"tokens": 100})
        assert event.type == SSEEventType.STAGE_PROGRESS
        assert event.payload["tokens"] == 100

    def test_stage_complete_convenience(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.stage_complete("executor")
        assert event.type == SSEEventType.STAGE_COMPLETE
        assert event.stage == "executor"

    def test_stage_failed_convenience(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.stage_failed("planner", "model unavailable")
        assert event.type == SSEEventType.STAGE_FAILED
        assert event.stage == "planner"
        assert event.payload["error"] == "model unavailable"

    def test_quality_scored_convenience(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.quality_scored(85, {"status": "pass"})
        assert event.type == SSEEventType.QUALITY_SCORED
        assert event.stage == "validate"
        assert event.payload["score"] == 85
        assert event.payload["status"] == "pass"

    def test_quality_decision_convenience(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.quality_decision("accept", {"score": 90})
        assert event.type == SSEEventType.QUALITY_DECISION
        assert event.stage == "validate"
        assert event.payload["decision"] == "accept"
        assert event.payload["score"] == 90

    def test_heartbeat_convenience(self) -> None:
        emitter = SSEEventEmitter("r1")
        event = emitter.heartbeat()
        assert event.type == SSEEventType.HEARTBEAT
        assert event.stage == "heartbeat"
        assert event.payload["status"] == "alive"

    def test_full_pipeline_sequence(self) -> None:
        """Simulate a complete pipeline run and verify sequence ordering."""
        emitter = SSEEventEmitter("run-full")
        events = [
            emitter.run_start({"prompt": "Create math plan"}),
            emitter.stage_start("planner"),
            emitter.stage_progress("planner", {"tokens": 50}),
            emitter.stage_complete("planner"),
            emitter.stage_start("validate"),
            emitter.quality_scored(85),
            emitter.quality_decision("accept"),
            emitter.stage_complete("validate"),
            emitter.stage_start("executor"),
            emitter.stage_complete("executor"),
            emitter.run_complete({"plan_id": "run-full"}),
        ]

        # Verify monotonically increasing sequence
        for i, event in enumerate(events):
            assert (
                event.seq == i + 1
            ), f"Event {i} has seq {event.seq}, expected {i + 1}"
            assert event.run_id == "run-full"

        # Verify terminal event
        assert events[-1].type == SSEEventType.RUN_COMPLETE

    def test_multiple_emitters_independent(self) -> None:
        """Two emitters for different runs don't share state."""
        e1 = SSEEventEmitter("run-a")
        e2 = SSEEventEmitter("run-b")

        e1.emit(SSEEventType.RUN_START, "init")
        e1.emit(SSEEventType.STAGE_START, "planner")
        e2.emit(SSEEventType.RUN_START, "init")

        assert e1.seq == 2
        assert e2.seq == 1


# ---------------------------------------------------------------------------
# SSEEventEmitter async thread safety (FINDING-22)
# ---------------------------------------------------------------------------


class TestSSEEventEmitterAsyncThreadSafety:
    """Verify async_emit produces monotonically increasing seq under concurrency."""

    @pytest.mark.asyncio
    async def test_async_emit_basic(self) -> None:

        emitter = SSEEventEmitter("async-run")
        event = await emitter.async_emit(SSEEventType.RUN_START, "init")
        assert event.seq == 1
        assert event.run_id == "async-run"

    @pytest.mark.asyncio
    async def test_concurrent_async_emit_no_duplicates(self) -> None:
        """Multiple concurrent async_emit calls should produce unique seq numbers."""
        import asyncio

        emitter = SSEEventEmitter("concurrent-run")
        results: list[SSEEvent] = []

        async def emit_n(n: int) -> None:
            for _ in range(n):
                event = await emitter.async_emit(SSEEventType.STAGE_PROGRESS, "test")
                results.append(event)

        # Run 5 concurrent emitters, each emitting 10 events
        await asyncio.gather(*[emit_n(10) for _ in range(5)])

        # Should have exactly 50 events
        assert len(results) == 50

        # All seq numbers should be unique
        seqs = [e.seq for e in results]
        assert len(set(seqs)) == 50

        # Seq numbers should be 1..50
        assert sorted(seqs) == list(range(1, 51))

    @pytest.mark.asyncio
    async def test_async_emit_with_payload(self) -> None:
        emitter = SSEEventEmitter("payload-run")
        event = await emitter.async_emit(
            SSEEventType.QUALITY_SCORED,
            "validate",
            {"score": 85},
        )
        assert event.payload == {"score": 85}
        assert event.seq == 1

    @pytest.mark.asyncio
    async def test_mixed_sync_async_emit(self) -> None:
        """Mixing sync emit and async_emit increments seq correctly."""
        emitter = SSEEventEmitter("mixed-run")
        e1 = emitter.emit(SSEEventType.RUN_START, "init")
        e2 = await emitter.async_emit(SSEEventType.STAGE_START, "planner")
        e3 = emitter.emit(SSEEventType.STAGE_COMPLETE, "planner")

        assert e1.seq == 1
        assert e2.seq == 2
        assert e3.seq == 3
