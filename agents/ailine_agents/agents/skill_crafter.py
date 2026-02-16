"""SkillCrafter Agent — helps teachers create custom skills conversationally.

Uses Pydantic AI Agent with output_type=CraftedSkillOutput.
No tools needed — pure conversational agent for skill authoring.
"""

from __future__ import annotations

import functools

import structlog
from pydantic_ai import Agent, RunContext

from ..deps import AgentDeps
from ..models import CraftedSkillOutput
from ._prompts import SKILLCRAFTER_SYSTEM_PROMPT

log = structlog.get_logger(__name__)

_DEFAULT_CRAFTER_MODEL = "anthropic:claude-sonnet-4-5"


def build_skill_crafter_agent(
    *,
    model: str | None = None,
) -> Agent[AgentDeps, CraftedSkillOutput]:
    """Create the SkillCrafter agent with typed output.

    Args:
        model: Override the default model ID.
    """
    agent: Agent[AgentDeps, CraftedSkillOutput] = Agent(
        model=model or _DEFAULT_CRAFTER_MODEL,
        output_type=CraftedSkillOutput,
        deps_type=AgentDeps,
        system_prompt=SKILLCRAFTER_SYSTEM_PROMPT,
        retries=2,
    )

    @agent.system_prompt
    async def add_context(ctx: RunContext[AgentDeps]) -> str:
        """Inject teacher/subject context into agent instructions."""
        parts: list[str] = []
        if ctx.deps.teacher_id:
            parts.append(f"Teacher ID: {ctx.deps.teacher_id}")
        if ctx.deps.subject:
            parts.append(f"Subject: {ctx.deps.subject}")
        return "\n".join(parts)

    return agent


@functools.lru_cache(maxsize=4)
def _build_and_cache_crafter(
    model: str | None = None,
) -> Agent[AgentDeps, CraftedSkillOutput]:
    """Build skill crafter agent (cached, thread-safe via lru_cache)."""
    return build_skill_crafter_agent(model=model)


def get_skill_crafter_agent(
    *,
    model: str | None = None,
) -> Agent[AgentDeps, CraftedSkillOutput]:
    """Get or create the singleton SkillCrafter agent."""
    if model is None:
        try:
            from ailine_runtime.shared.config import get_settings

            model = getattr(get_settings(), "crafter_model", None)
        except (ImportError, AttributeError):
            pass

    return _build_and_cache_crafter(model)


def reset_skill_crafter_agent() -> None:
    """Reset singleton (for testing)."""
    _build_and_cache_crafter.cache_clear()
