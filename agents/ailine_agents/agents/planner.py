"""PlannerAgent — generates structured study plan drafts.

Uses Pydantic AI Agent with output_type=StudyPlanDraft.
Tools: rag_search, curriculum_lookup.
"""

from __future__ import annotations

import functools

import structlog
from ailine_runtime.domain.entities.plan import StudyPlanDraft
from pydantic_ai import Agent, RunContext

from ..deps import AgentDeps
from ._prompts import PLANNER_SYSTEM_PROMPT
from ._tool_bridge import register_tools

log = structlog.get_logger(__name__)

_PLANNER_SKILLS = ["lesson-planner", "accessibility-coach"]


@functools.lru_cache(maxsize=1)
def _cached_skill_fragment() -> str:
    """Load and cache skill prompt fragments (scanned once per process)."""
    from ..skills.registry import SkillRegistry

    registry = SkillRegistry()
    registry.scan_paths()
    return registry.get_prompt_fragment(_PLANNER_SKILLS)


_DEFAULT_PLANNER_MODEL = "anthropic:claude-opus-4-6"


def build_planner_agent(
    *,
    use_skills: bool = True,
    model: str | None = None,
) -> Agent[AgentDeps, StudyPlanDraft]:
    """Create the PlannerAgent with typed output and tools.

    Args:
        use_skills: Whether to load skill prompt fragments.
        model: Override the default model ID (e.g. for testing or SmartRouter).
    """
    agent: Agent[AgentDeps, StudyPlanDraft] = Agent(
        model=model or _DEFAULT_PLANNER_MODEL,
        output_type=StudyPlanDraft,
        deps_type=AgentDeps,
        system_prompt=PLANNER_SYSTEM_PROMPT,
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
        if parts:
            parts.append("When calling rag_search, ALWAYS pass teacher_id.")
        return "\n".join(parts)

    if use_skills:

        @agent.system_prompt
        async def add_skills(ctx: RunContext[AgentDeps]) -> str:
            """Load cached skill instructions (lesson-planner + accessibility-coach)."""
            fragment = _cached_skill_fragment()
            if fragment:
                log.debug("planner_skills_loaded", skills=_PLANNER_SKILLS)
            return fragment

    return agent


@functools.lru_cache(maxsize=4)
def _build_and_register_planner(
    use_skills: bool, model: str | None = None
) -> Agent[AgentDeps, StudyPlanDraft]:
    """Build planner agent with tools (cached, thread-safe via lru_cache)."""
    agent = build_planner_agent(use_skills=use_skills, model=model)
    from ailine_runtime.tools.registry import build_tool_registry

    register_tools(
        agent,
        build_tool_registry(),
        allowed_names=["rag_search", "curriculum_lookup"],
    )
    return agent


def get_planner_agent(
    *,
    use_skills: bool | None = None,
    model: str | None = None,
) -> Agent[AgentDeps, StudyPlanDraft]:
    """Get or create the singleton PlannerAgent with tools registered."""
    if use_skills is None:
        try:
            from ailine_runtime.shared.config import get_settings

            use_skills = get_settings().planner_use_skills
        except (ImportError, AttributeError):
            use_skills = True

    if model is None:
        try:
            from ailine_runtime.shared.config import get_settings

            model = getattr(get_settings(), "planner_model", None)
        except (ImportError, AttributeError):
            pass

    return _build_and_register_planner(use_skills, model)


def reset_planner_agent() -> None:
    """Reset singleton (for testing)."""
    _build_and_register_planner.cache_clear()
    _cached_skill_fragment.cache_clear()
