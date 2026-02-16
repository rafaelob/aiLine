"""TutorAgent — handles 1:1 student chat sessions.

Uses Pydantic AI Agent with output_type=TutorTurnOutput.
Tools: rag_search, web_search.
"""

from __future__ import annotations

import functools
from typing import Any

import structlog
from ailine_runtime.domain.entities.tutor import TutorTurnOutput
from pydantic_ai import Agent, RunContext

from ..deps import AgentDeps
from ._prompts import TUTOR_BASE_SYSTEM_PROMPT
from ._tool_bridge import register_tools

log = structlog.get_logger(__name__)

_TUTOR_SKILLS = ["socratic-tutor"]


@functools.lru_cache(maxsize=1)
def _cached_tutor_skill_fragment() -> str:
    """Load and cache tutor skill prompt fragments (scanned once per process)."""
    from ..skills.registry import SkillRegistry

    registry = SkillRegistry()
    registry.scan_paths()
    return registry.get_prompt_fragment(_TUTOR_SKILLS)


_DEFAULT_TUTOR_MODEL = "anthropic:claude-sonnet-4-5"


def build_tutor_agent(
    *,
    use_skills: bool = True,
    model: str | None = None,
) -> Agent[AgentDeps, TutorTurnOutput]:
    """Create the TutorAgent with typed output, RAG tool, and web search.

    Args:
        use_skills: Whether to load skill prompt fragments.
        model: Override the default model ID (e.g. for testing or SmartRouter).
    """
    agent: Agent[AgentDeps, TutorTurnOutput] = Agent(
        model=model or _DEFAULT_TUTOR_MODEL,
        output_type=TutorTurnOutput,
        deps_type=AgentDeps,
        system_prompt=TUTOR_BASE_SYSTEM_PROMPT,
        retries=2,
    )

    @agent.system_prompt
    async def add_context(ctx: RunContext[AgentDeps]) -> str:
        """Inject teacher/subject context for RAG scoping."""
        parts: list[str] = []
        if ctx.deps.teacher_id:
            parts.append(f"Teacher ID: {ctx.deps.teacher_id}")
        if ctx.deps.subject:
            parts.append(f"Subject: {ctx.deps.subject}")
        return "\n".join(parts)

    if use_skills:

        @agent.system_prompt
        async def add_skills(ctx: RunContext[AgentDeps]) -> str:
            """Load cached skill instructions (socratic-tutor)."""
            fragment = _cached_tutor_skill_fragment()
            if fragment:
                log.debug("tutor_skills_loaded", skills=_TUTOR_SKILLS)
            return fragment

    @agent.tool
    async def web_search(ctx: RunContext[AgentDeps], query: str) -> dict[str, Any]:
        """Search the web for current educational information.

        Use this tool when the student asks about recent events, needs
        up-to-date facts, or when your knowledge might be outdated.
        Returns text with cited sources.

        Args:
            query: The search query (be specific and educational).
        """
        if ctx.deps.llm is None:
            return {"error": "No LLM configured for web search"}
        if not ctx.deps.llm.capabilities.get("web_search"):
            return {
                "text": "Web search is not available with the current provider.",
                "sources": [],
            }
        result = await ctx.deps.llm.generate_with_search(query)
        return {
            "text": result.text,
            "sources": [
                {"url": s.url, "title": s.title, "snippet": s.snippet}
                for s in result.sources
            ],
        }

    return agent


@functools.lru_cache(maxsize=4)
def _build_and_register_tutor(
    use_skills: bool, model: str | None = None
) -> Agent[AgentDeps, TutorTurnOutput]:
    """Build tutor agent with tools (cached, thread-safe via lru_cache)."""
    agent = build_tutor_agent(use_skills=use_skills, model=model)
    from ailine_runtime.tools.registry import build_tool_registry

    register_tools(
        agent,
        build_tool_registry(),
        allowed_names=["rag_search"],
    )
    return agent


def get_tutor_agent(
    *,
    use_skills: bool | None = None,
    model: str | None = None,
) -> Agent[AgentDeps, TutorTurnOutput]:
    """Get or create the singleton TutorAgent with tools registered."""
    if use_skills is None:
        try:
            from ailine_runtime.shared.config import get_settings

            use_skills = get_settings().persona_use_skills
        except (ImportError, AttributeError):
            use_skills = True

    if model is None:
        try:
            from ailine_runtime.shared.config import get_settings

            model = getattr(get_settings(), "tutor_model", None)
        except (ImportError, AttributeError):
            pass

    return _build_and_register_tutor(use_skills, model)


def reset_tutor_agent() -> None:
    """Reset singleton (for testing)."""
    _build_and_register_tutor.cache_clear()
    _cached_tutor_skill_fragment.cache_clear()
