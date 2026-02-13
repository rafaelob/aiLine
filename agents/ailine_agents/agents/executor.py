"""ExecutorAgent — finalizes plans via tool calls (ADR-048: replaces Claude Agent SDK).

Uses Pydantic AI Agent with output_type=ExecutorResult.
Tools: accessibility_checklist, export_variant, save_plan, curriculum_lookup.
"""

from __future__ import annotations

import functools

from pydantic_ai import Agent, RunContext

from ..deps import AgentDeps
from ..models import ExecutorResult
from ._prompts import EXECUTOR_SYSTEM_PROMPT
from ._tool_bridge import register_tools


def build_executor_agent() -> Agent[AgentDeps, ExecutorResult]:
    """Create the ExecutorAgent with typed output and tools."""
    agent: Agent[AgentDeps, ExecutorResult] = Agent(
        model="anthropic:claude-sonnet-4-5",
        output_type=ExecutorResult,
        deps_type=AgentDeps,
        system_prompt=EXECUTOR_SYSTEM_PROMPT,
        retries=2,
    )

    @agent.system_prompt
    async def add_context(ctx: RunContext[AgentDeps]) -> str:
        """Inject run context (run_id, variants) into agent instructions."""
        parts: list[str] = []
        if ctx.deps.run_id:
            parts.append(f"run_id: {ctx.deps.run_id}")
        if ctx.deps.default_variants:
            parts.append(f"variants: {ctx.deps.default_variants}")
        if ctx.deps.teacher_id:
            parts.append(f"teacher_id: {ctx.deps.teacher_id}")
        return "\n".join(parts)

    return agent


@functools.lru_cache(maxsize=1)
def _build_and_register_executor() -> Agent[AgentDeps, ExecutorResult]:
    """Build executor agent with tools (cached, thread-safe via lru_cache)."""
    agent = build_executor_agent()
    from ailine_runtime.tools.registry import build_tool_registry

    register_tools(
        agent,
        build_tool_registry(),
        allowed_names=[
            "accessibility_checklist",
            "export_variant",
            "save_plan",
            "curriculum_lookup",
        ],
    )
    return agent


def get_executor_agent() -> Agent[AgentDeps, ExecutorResult]:
    """Get or create the singleton ExecutorAgent with tools registered."""
    return _build_and_register_executor()


def reset_executor_agent() -> None:
    """Reset singleton (for testing)."""
    _build_and_register_executor.cache_clear()
