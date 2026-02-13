"""SSE streaming endpoint for plan generation.

POST /plans/generate/stream
Streams typed SSE events (14 types) as the pipeline progresses.

ADR-006: SSE for pipeline, WebSocket for tutor.
ADR-024: Typed SSE event contract.
ADR-038: LangGraph custom stream_mode.
ADR-042: Explicit recursion_limit=25.
"""

from __future__ import annotations

import asyncio
import contextlib
import traceback
from collections.abc import AsyncIterator
from typing import Any

import structlog
from ailine_agents import AgentDepsFactory
from ailine_agents.workflows.plan_workflow import build_plan_workflow
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ...shared.sanitize import sanitize_prompt, validate_teacher_id
from ...shared.tenant import try_get_current_teacher_id
from ...shared.trace_store import get_trace_store
from ...workflow.plan_workflow import DEFAULT_RECURSION_LIMIT, RunState
from ..streaming.events import SSEEventEmitter

logger = structlog.get_logger("ailine.api.plans_stream")

router = APIRouter()

# Heartbeat interval to keep the connection alive (seconds).
_HEARTBEAT_INTERVAL_S = 15.0


def _resolve_teacher_id(body_teacher_id: str | None) -> str:
    """Resolve teacher_id: middleware context takes precedence over body."""
    ctx_teacher_id = try_get_current_teacher_id()
    if ctx_teacher_id:
        return ctx_teacher_id
    if body_teacher_id:
        try:
            return validate_teacher_id(body_teacher_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ""


class PlanStreamIn(BaseModel):
    """Request body for streaming plan generation."""

    run_id: str = Field(..., description="Client-generated run ID for observability.")
    user_prompt: str = Field(..., min_length=1, description="Teacher's natural-language request.")
    teacher_id: str | None = Field(None, description="Optional: teacher ID (needed for RAG).")
    subject: str | None = Field(None, description="Optional: subject (RAG filter).")
    class_accessibility_profile: dict[str, Any] | None = Field(
        None, description="Accessibility profile for the class."
    )
    learner_profiles: list[dict[str, Any]] | None = Field(
        None, description="Anonymous learner profiles for differentiation."
    )


async def _heartbeat_loop(
    emitter: SSEEventEmitter,
    queue: asyncio.Queue[dict[str, str] | None],
    interval: float = _HEARTBEAT_INTERVAL_S,
) -> None:
    """Push heartbeat events into the queue at a fixed interval.

    Stops when ``None`` is placed in the queue (sentinel).
    """
    try:
        while True:
            await asyncio.sleep(interval)
            event = emitter.heartbeat()
            await queue.put({"data": event.to_sse_data()})
    except asyncio.CancelledError:
        return  # Graceful shutdown: pipeline finished, heartbeat no longer needed


async def _run_pipeline(
    body: PlanStreamIn,
    teacher_id: str,
    settings: Any,
    container: Any,
    emitter: SSEEventEmitter,
    queue: asyncio.Queue[dict[str, str] | None],
) -> None:
    """Execute the LangGraph plan workflow, pushing SSE events to the queue."""
    try:
        # Initialize trace
        trace_store = get_trace_store()
        await trace_store.get_or_create(body.run_id)

        deps = AgentDepsFactory.from_container(
            container,
            teacher_id=teacher_id,
            run_id=body.run_id,
            subject=body.subject or "",
            default_variants=getattr(settings, "default_variants", "standard_html"),
            max_refinement_iters=getattr(settings, "max_refinement_iters", 2),
            emitter=emitter,
        )
        workflow = build_plan_workflow(deps)

        # Synchronous writer callback: puts events into the async queue.
        # Because LangGraph node functions are already async, this runs
        # inside the same event loop -- asyncio.Queue.put_nowait is safe.
        def stream_writer(event: Any) -> None:
            queue.put_nowait({"data": event.to_sse_data()})

        init_state: RunState = {
            "run_id": body.run_id,
            "user_prompt": body.user_prompt,
            "teacher_id": teacher_id or body.teacher_id,
            "subject": body.subject,
            "class_accessibility_profile": body.class_accessibility_profile,
            "learner_profiles": body.learner_profiles,
            "refine_iter": 0,
        }

        config = {
            "recursion_limit": DEFAULT_RECURSION_LIMIT,
            "configurable": {
                "sse_emitter": emitter,
                "stream_writer": stream_writer,
            },
        }

        # Emit run start
        start_event = emitter.run_start({"prompt": body.user_prompt[:200]})
        await queue.put({"data": start_event.to_sse_data()})

        # Execute the full workflow
        final_state = await workflow.ainvoke(init_state, config=config)

        # Emit run complete with summary payload
        final_payload: dict[str, Any] = {"plan_id": body.run_id}
        final_data = final_state.get("final") or {}
        if isinstance(final_data, dict):
            parsed = final_data.get("parsed")
            if isinstance(parsed, dict):
                final_payload["score"] = parsed.get("score")
                final_payload["human_review_required"] = parsed.get("human_review_required")

        complete_event = emitter.run_complete(final_payload)
        await queue.put({"data": complete_event.to_sse_data()})

        # Finalize trace
        await trace_store.update_run(
            body.run_id,
            status="completed",
            final_score=final_payload.get("score"),
        )

    except Exception as exc:
        logger.error("pipeline_failed", run_id=body.run_id, error=str(exc), tb=traceback.format_exc())
        error_event = emitter.run_failed(str(exc), stage="pipeline")
        await queue.put({"data": error_event.to_sse_data()})

        # Mark trace as failed
        await trace_store.update_run(body.run_id, status="failed")

    finally:
        # Sentinel to signal the generator to stop
        await queue.put(None)


@router.post("/generate/stream")
async def plans_generate_stream(body: PlanStreamIn, request: Request) -> EventSourceResponse:
    """Stream plan generation progress as Server-Sent Events.

    The response is an SSE stream where each event carries the
    standard envelope: {run_id, seq, ts, type, stage, payload}.
    The stream always terminates with either ``run.completed``
    or ``run.failed`` before closing.
    """
    container = request.app.state.container
    settings = request.app.state.settings

    # --- Input sanitization ---
    body.user_prompt = sanitize_prompt(body.user_prompt)
    if not body.user_prompt:
        raise HTTPException(status_code=422, detail="user_prompt must not be empty after sanitization")

    # Resolve teacher_id: middleware > body
    teacher_id = _resolve_teacher_id(body.teacher_id)

    emitter = SSEEventEmitter(body.run_id)
    queue: asyncio.Queue[dict[str, str] | None] = asyncio.Queue()

    async def event_generator() -> AsyncIterator[dict[str, str]]:
        # Start the pipeline and heartbeat as background tasks
        pipeline_task = asyncio.create_task(
            _run_pipeline(body, teacher_id, settings, container, emitter, queue)
        )
        heartbeat_task = asyncio.create_task(
            _heartbeat_loop(emitter, queue)
        )

        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():  # pragma: no cover
                    logger.info("client_disconnected", run_id=body.run_id)
                    break

                try:
                    item = await asyncio.wait_for(queue.get(), timeout=1.0)
                except TimeoutError:  # pragma: no cover
                    continue

                if item is None:
                    # Pipeline finished (sentinel)
                    break

                yield item
        finally:
            heartbeat_task.cancel()
            if not pipeline_task.done():  # pragma: no cover
                pipeline_task.cancel()
            # Suppress CancelledError from background tasks
            for task in (heartbeat_task, pipeline_task):
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await task

    return EventSourceResponse(
        event_generator(),
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache, no-store",
            "Connection": "keep-alive",
        },
    )
