"""Plan generation workflow: PlannerAgent -> QualityGate -> Refine -> ExecutorAgent.

Pydantic AI agents called inside LangGraph nodes. SSE streaming preserved.
ADR-038: LangGraph custom stream_mode for SSE.
ADR-042: Explicit recursion_limit=25.
ADR-048: No Claude Agent SDK -- direct Pydantic AI agents.
ADR-050: Tiered quality gate (<60/60-79/>=80).

Resilience features:
- Retry with exponential backoff on transient LLM errors.
- Circuit breaker prevents cascading failures.
- Workflow timeout aborts gracefully after max_workflow_duration_seconds.
- Idempotency key prevents duplicate plan generations.
- Structured logging with run_id, stage, model, and duration.

Node implementations live in _plan_nodes.py for maintainability.
"""

from __future__ import annotations

from typing import Any

from ailine_runtime.api.streaming.events import SSEEventType
from ailine_runtime.shared.observability import log_event
from langgraph.graph import END, StateGraph
from langgraph.types import RunnableConfig

from ..agents.executor import get_executor_agent
from ..agents.planner import get_planner_agent
from ..deps import AgentDeps
from ..model_selection.bridge import PydanticAIModelSelector
from ..resilience import IdempotencyGuard
from ._plan_nodes import (
    WorkflowTimeoutError,
    make_executor_node,
    make_planner_node,
    make_validate_node,
)
from ._sse_helpers import get_emitter_and_writer, try_emit
from ._state import RunState

__all__ = ["WorkflowTimeoutError", "build_plan_workflow", "get_idempotency_guard"]

# Module-level idempotency guard (single-process).
_idempotency_guard = IdempotencyGuard()


def build_plan_workflow(
    deps: AgentDeps,
    *,
    model_selector: PydanticAIModelSelector | None = None,
) -> Any:
    """Build LangGraph plan workflow using Pydantic AI agents.

    Args:
        deps: AgentDeps (from AgentDepsFactory).
        model_selector: Optional SmartRouter -> Pydantic AI model bridge.

    Returns:
        Compiled LangGraph StateGraph.
    """
    graph = StateGraph(RunState)
    planner = get_planner_agent()
    executor = get_executor_agent()

    # Build node functions from extracted helpers
    planner_node = make_planner_node(planner, deps, model_selector)
    validate_node = make_validate_node(deps, model_selector)
    executor_node = make_executor_node(executor, deps, model_selector)

    def decision_node(state: RunState, config: RunnableConfig) -> RunState:
        """Emit quality decision event."""
        emitter, writer = get_emitter_and_writer(config)
        try:
            v = state.get("validation") or {}
            score = int(v.get("score") or 0)
            refine_iter = int(state.get("refine_iter") or 0)

            if score < 60 and refine_iter < deps.max_refinement_iters:
                decision = "must-refine"
            elif score < 80 and refine_iter < deps.max_refinement_iters:
                decision = "refine-if-budget"
            else:
                decision = "accept"

            decision_payload = {
                "decision": decision,
                "score": score,
                "iteration": refine_iter,
            }
            try_emit(emitter, writer, SSEEventType.QUALITY_DECISION, "validate", decision_payload)
            return {"quality_decision": decision_payload}
        except Exception as exc:
            log_event("decision.failed", run_id=state.get("run_id", ""), error=str(exc))
            try_emit(emitter, writer, SSEEventType.STAGE_FAILED, "decision", {"error": str(exc)})
            raise

    def bump_refine_iter(state: RunState) -> RunState:
        new_iter = int(state.get("refine_iter") or 0) + 1
        log_event("refine.bump", run_id=state.get("run_id", ""), iteration=new_iter)
        return {"refine_iter": new_iter}

    def should_execute(state: RunState) -> str:
        """Route based on tiered quality gate (ADR-050)."""
        v = state.get("validation") or {}
        score = int(v.get("score") or 0)
        refine_iter = int(state.get("refine_iter") or 0)

        if score < 60 and refine_iter < deps.max_refinement_iters:
            return "refine"
        if score < 80 and refine_iter < deps.max_refinement_iters:
            return "refine"
        return "execute"

    graph.add_node("planner", planner_node)
    graph.add_node("validate", validate_node)
    graph.add_node("decision", decision_node)
    graph.add_node("bump_refine", bump_refine_iter)
    graph.add_node("executor", executor_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "validate")
    graph.add_edge("validate", "decision")
    graph.add_conditional_edges(
        "decision",
        should_execute,
        {"refine": "bump_refine", "execute": "executor"},
    )
    graph.add_edge("bump_refine", "planner")
    graph.add_edge("executor", END)

    return graph.compile()


def get_idempotency_guard() -> IdempotencyGuard:
    """Access the module-level idempotency guard (for testing/reset)."""
    return _idempotency_guard
