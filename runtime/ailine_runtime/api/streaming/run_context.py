"""Run-level SSE context manager guaranteeing terminal events (ADR-055).

Wraps a pipeline execution to ensure that either run.completed or run.failed
is always emitted, even on unhandled exceptions or cancellation.

The terminal event is emitted exactly once (idempotent via replay store marker).
"""

from __future__ import annotations

import asyncio
from typing import Any

from ...shared.observability import get_logger
from .events import SSEEvent, SSEEventEmitter, SSEEventType
from .replay import InMemoryReplayStore

_log = get_logger("ailine.streaming.run_context")

# Type alias for event sink callback
EventSink = Any  # Callable[[SSEEvent], None] or async queue


class RunContext:
    """Async context manager that guarantees terminal SSE events.

    Usage::

        async with RunContext(run_id, emitter, sink, replay_store) as ctx:
            # Pipeline execution happens here
            await ctx.emit_stage_start("planner")
            # ... do work ...
            await ctx.emit_stage_complete("planner")
            # If an exception occurs, run.failed is emitted automatically

    The context manager:
    1. Emits run.started on __aenter__
    2. Emits run.completed on normal exit
    3. Emits run.failed on exception (including CancelledError)
    4. Guarantees exactly-once terminal event via replay store marker
    """

    def __init__(
        self,
        run_id: str,
        emitter: SSEEventEmitter,
        sink: EventSink,
        replay_store: InMemoryReplayStore | None = None,
    ) -> None:
        self._run_id = run_id
        self._emitter = emitter
        self._sink = sink
        self._replay = replay_store or InMemoryReplayStore()
        self._finalized = False

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def emitter(self) -> SSEEventEmitter:
        return self._emitter

    async def _push(self, event: SSEEvent) -> None:
        """Push event to sink and replay store."""
        payload_json = event.to_sse_data()
        await self._replay.append(self._run_id, event.seq, payload_json)

        if isinstance(self._sink, asyncio.Queue):
            await self._sink.put({"data": payload_json})
        elif callable(self._sink):
            self._sink(event)

    async def emit(
        self,
        event_type: SSEEventType,
        stage: str,
        payload: dict[str, Any] | None = None,
    ) -> SSEEvent:
        """Emit an SSE event through the context."""
        event = self._emitter.emit(event_type, stage, payload)
        await self._push(event)
        return event

    async def emit_stage_start(
        self, stage: str, payload: dict[str, Any] | None = None
    ) -> SSEEvent:
        return await self.emit(SSEEventType.STAGE_START, stage, payload)

    async def emit_stage_complete(
        self, stage: str, payload: dict[str, Any] | None = None
    ) -> SSEEvent:
        return await self.emit(SSEEventType.STAGE_COMPLETE, stage, payload)

    async def emit_stage_failed(self, stage: str, error: str) -> SSEEvent:
        return await self.emit(SSEEventType.STAGE_FAILED, stage, {"error": error})

    async def _finalize_ok(self) -> None:
        """Emit run.completed exactly once."""
        if self._finalized:
            return
        is_first = await self._replay.mark_terminal(self._run_id, "completed")
        if is_first:
            event = self._emitter.run_complete()
            await self._push(event)
        self._finalized = True

    async def _finalize_error(self, exc: BaseException) -> None:
        """Emit run.failed exactly once."""
        if self._finalized:
            return
        is_first = await self._replay.mark_terminal(self._run_id, "failed")
        if is_first:
            error_msg = f"{exc.__class__.__name__}: {exc}"
            event = self._emitter.run_failed(error_msg, stage="pipeline")
            await self._push(event)
        self._finalized = True

    async def __aenter__(self) -> RunContext:
        """Emit run.started and return context."""
        event = self._emitter.run_start()
        await self._push(event)
        _log.info("run_context.started", run_id=self._run_id)
        return self

    async def __aexit__(
        self, exc_type: type | None, exc: BaseException | None, tb: Any
    ) -> bool | None:
        """Guarantee terminal event emission."""
        if exc is None:
            await self._finalize_ok()
            _log.info("run_context.completed", run_id=self._run_id)
        else:
            await self._finalize_error(exc)
            _log.error(
                "run_context.failed",
                run_id=self._run_id,
                error=str(exc),
                error_type=exc.__class__.__name__,
            )
        return None  # Don't suppress exceptions
