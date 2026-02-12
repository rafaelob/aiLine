"""SSE emission helpers for LangGraph workflow nodes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ailine_runtime.api.streaming.events import SSEEvent, SSEEventEmitter, SSEEventType
from langgraph.types import RunnableConfig


def get_emitter_and_writer(
    config: RunnableConfig,
) -> tuple[SSEEventEmitter | None, Callable[[SSEEvent], None] | None]:
    """Extract SSE emitter/writer from LangGraph configurable."""
    configurable = config.get("configurable", {})
    emitter = configurable.get("sse_emitter")
    writer = configurable.get("stream_writer")
    if emitter is not None and writer is not None:
        return emitter, writer
    return None, None


def try_emit(
    emitter: SSEEventEmitter | None,
    writer: Callable[[SSEEvent], None] | None,
    event_type: SSEEventType,
    stage: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Emit an SSE event if streaming is active; no-op otherwise."""
    if emitter is not None and writer is not None:
        event = emitter.emit(event_type, stage, payload)
        writer(event)
