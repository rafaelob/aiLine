"""Executor node for the plan generation LangGraph workflow.

Contains the make_executor_node factory and the executor prompt builder.
"""

from __future__ import annotations

import json
import time
from typing import Any

from ailine_runtime.api.streaming.events import SSEEventType
from ailine_runtime.shared.observability import log_event
from langgraph.types import RunnableConfig
from pydantic_ai import Agent

from ..deps import AgentDeps
from ..model_selection.bridge import PydanticAIModelSelector
from ._node_shared import (
    _check_timeout,
    _log_node_success,
    _run_agent_with_resilience,
    _select_model,
)
from ._sse_helpers import get_emitter_and_writer, try_emit
from ._state import RunState
from ._trace_capture import build_route_rationale, capture_node_trace

__all__ = [
    "build_executor_prompt",
    "make_executor_node",
]


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
            task_type="executor",
            model_name=model_name,
            model_selector=model_selector,
        )
        try_emit(
            emitter,
            writer,
            SSEEventType.STAGE_START,
            "executor",
            {
                "route_rationale": exec_rationale,
            },
        )

        draft_json = state.get("draft") or {}
        prompt = build_executor_prompt(
            draft_json,
            run_id,
            state.get("class_accessibility_profile"),
            deps.default_variants,
        )

        async def _run():
            return await executor.run(
                prompt,
                deps=deps,
                **({"model": model_override} if model_override else {}),
            )

        result = await _run_agent_with_resilience(
            agent_fn=_run,
            deps=deps,
            stage="executor",
            run_id=run_id,
            stage_start=stage_start,
            emitter=emitter,
            writer=writer,
        )

        duration_ms = (time.monotonic() - stage_start) * 1000
        _log_node_success(
            stage="executor",
            run_id=run_id,
            model_name=model_name,
            duration_ms=duration_ms,
            metadata={"plan_id": run_id},
        )
        try_emit(
            emitter,
            writer,
            SSEEventType.STAGE_COMPLETE,
            "executor",
            {"plan_id": run_id},
        )

        await capture_node_trace(
            run_id=run_id,
            node_name="executor",
            status="success",
            time_ms=duration_ms,
            inputs_summary={"draft_keys": list(draft_json.keys())[:10]},
            outputs_summary={"plan_id": run_id},
            route_rationale=exec_rationale,
        )

        return {"final": result.output.model_dump()}  # type: ignore[typeddict-item,return-value]  # LangGraph partial state update

    return executor_node
