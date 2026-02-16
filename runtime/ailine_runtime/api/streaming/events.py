"""Typed SSE event system for the plan generation pipeline.

Defines the 14 SSE event types, the event envelope (SSEEvent),
and the SSEEventEmitter that manages run-scoped sequencing.

ADR-024: Typed SSE event contract -- lifecycle + quality + tool events with seq/run_id.
ADR-038: LangGraph custom stream_mode for SSE -- get_stream_writer() gives full control.
FINDING-22: Thread-safe emission with asyncio.Lock for parallel LangGraph branches.
"""

from __future__ import annotations

import asyncio
import json
import threading
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SSEEventType(StrEnum):
    """All 14 SSE event types as defined in SYSTEM_DESIGN.md."""

    # Run lifecycle
    RUN_START = "run.started"
    RUN_COMPLETE = "run.completed"
    RUN_FAILED = "run.failed"

    # Stage lifecycle
    STAGE_START = "stage.started"
    STAGE_PROGRESS = "stage.progress"
    STAGE_COMPLETE = "stage.completed"
    STAGE_FAILED = "stage.failed"

    # Quality gate
    QUALITY_SCORED = "quality.scored"
    QUALITY_DECISION = "quality.decision"

    # Refinement
    REFINEMENT_START = "refinement.started"
    REFINEMENT_COMPLETE = "refinement.completed"

    # Tool calls (Glass Box)
    TOOL_START = "tool.started"
    TOOL_COMPLETE = "tool.completed"

    # AI Receipt (trust chain summary)
    AI_RECEIPT = "ai_receipt"

    # Heartbeat
    HEARTBEAT = "heartbeat"


class SSEEvent(BaseModel):
    """SSE event envelope: {run_id, seq, ts, type, stage, payload}.

    Every event carries a monotonically increasing sequence number
    within a single run, enabling the frontend to detect gaps and
    reorder if needed.
    """

    run_id: str
    seq: int
    ts: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    type: SSEEventType
    stage: str
    payload: dict[str, Any] = Field(default_factory=dict)

    def to_sse_data(self) -> str:
        """Serialize to JSON string suitable for SSE data field."""
        return json.dumps(self.model_dump(), ensure_ascii=False)


class SSEEventEmitter:
    """Manages SSE event sequencing for a single pipeline run.

    Thread-safe for concurrent async emission: an asyncio.Lock ensures
    that sequence numbers are always monotonically increasing even when
    parallel LangGraph branches emit concurrently (FINDING-22).

    The emitter holds no I/O references -- it only produces SSEEvent
    instances; the caller decides how to send them (EventSourceResponse,
    LangGraph get_stream_writer(), etc.).
    """

    def __init__(self, run_id: str) -> None:
        self._run_id = run_id
        self._seq = 0
        self._lock = asyncio.Lock()
        self._sync_lock = threading.Lock()

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def seq(self) -> int:
        """Current sequence number (last emitted)."""
        return self._seq

    def emit(
        self,
        event_type: SSEEventType,
        stage: str,
        payload: dict[str, Any] | None = None,
    ) -> SSEEvent:
        """Create the next SSEEvent with auto-incremented seq.

        For synchronous contexts (LangGraph node callbacks).
        Thread-safe via threading.Lock for concurrent emission from
        parallel LangGraph branches.
        """
        with self._sync_lock:
            self._seq += 1
            return SSEEvent(
                run_id=self._run_id,
                seq=self._seq,
                type=event_type,
                stage=stage,
                payload=payload or {},
            )

    async def async_emit(
        self,
        event_type: SSEEventType,
        stage: str,
        payload: dict[str, Any] | None = None,
    ) -> SSEEvent:
        """Create the next SSEEvent with atomic async locking.

        Use this when multiple async tasks (e.g. parallel LangGraph branches)
        may emit concurrently to guarantee monotonically increasing seq numbers.
        """
        async with self._lock:
            self._seq += 1
            return SSEEvent(
                run_id=self._run_id,
                seq=self._seq,
                type=event_type,
                stage=stage,
                payload=payload or {},
            )

    def run_start(self, payload: dict[str, Any] | None = None) -> SSEEvent:
        """Convenience: emit RUN_START."""
        return self.emit(SSEEventType.RUN_START, "init", payload)

    def run_complete(self, payload: dict[str, Any] | None = None) -> SSEEvent:
        """Convenience: emit RUN_COMPLETE."""
        return self.emit(SSEEventType.RUN_COMPLETE, "done", payload)

    def run_failed(self, error: str, stage: str = "unknown") -> SSEEvent:
        """Convenience: emit RUN_FAILED with error message."""
        return self.emit(SSEEventType.RUN_FAILED, stage, {"error": error})

    def stage_start(
        self, stage: str, payload: dict[str, Any] | None = None
    ) -> SSEEvent:
        return self.emit(SSEEventType.STAGE_START, stage, payload)

    def stage_progress(
        self, stage: str, payload: dict[str, Any] | None = None
    ) -> SSEEvent:
        return self.emit(SSEEventType.STAGE_PROGRESS, stage, payload)

    def stage_complete(
        self, stage: str, payload: dict[str, Any] | None = None
    ) -> SSEEvent:
        return self.emit(SSEEventType.STAGE_COMPLETE, stage, payload)

    def stage_failed(self, stage: str, error: str) -> SSEEvent:
        return self.emit(SSEEventType.STAGE_FAILED, stage, {"error": error})

    def quality_scored(
        self, score: int, payload: dict[str, Any] | None = None
    ) -> SSEEvent:
        merged = {"score": score}
        if payload:
            merged.update(payload)
        return self.emit(SSEEventType.QUALITY_SCORED, "validate", merged)

    def quality_decision(
        self, decision: str, payload: dict[str, Any] | None = None
    ) -> SSEEvent:
        merged = {"decision": decision}
        if payload:
            merged.update(payload)
        return self.emit(SSEEventType.QUALITY_DECISION, "validate", merged)

    def ai_receipt(self, payload: dict[str, Any] | None = None) -> SSEEvent:
        """Convenience: emit AI_RECEIPT with trust chain summary."""
        return self.emit(SSEEventType.AI_RECEIPT, "receipt", payload)

    def heartbeat(self) -> SSEEvent:
        return self.emit(SSEEventType.HEARTBEAT, "heartbeat", {"status": "alive"})
