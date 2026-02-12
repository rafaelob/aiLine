"""TutorAgent — handles 1:1 student chat sessions.

Uses Pydantic AI Agent with output_type=TutorTurnOutput.
Tools: rag_search, web_search.
"""

from __future__ import annotations

from typing import Any

import structlog
from ailine_runtime.domain.entities.tutor import TutorTurnOutput
from pydantic_ai import Agent, RunContext

from ..deps import AgentDeps
from ..skills.registry import SkillRegistry
from ._prompts import TUTOR_BASE_SYSTEM_PROMPT
from ._tool_bridge import register_tools

log = structlog.get_logger(__name__)

_TUTOR_SKILLS = ["socratic-tutor"]


def build_tutor_agent(*, use_skills: bool = True) -> Agent[AgentDeps, TutorTurnOutput]:
    """Create the TutorAgent with typed output, RAG tool, and web search."""
    agent: Agent[AgentDeps, TutorTurnOutput] = Agent(
        model="anthropic:claude-sonnet-4-5",
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
            """Load skill instructions (socratic-tutor)."""
            registry = SkillRegistry()
            registry.scan_paths()
            fragment = registry.get_prompt_fragment(_TUTOR_SKILLS)
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


_tutor_agent: Agent[AgentDeps, TutorTurnOutput] | None = None


def get_tutor_agent(*, use_skills: bool | None = None) -> Agent[AgentDeps, TutorTurnOutput]:
    """Get or create the singleton TutorAgent with tools registered."""
    global _tutor_agent
    if _tutor_agent is None:
        if use_skills is None:
            try:
                from ailine_runtime.shared.config import get_settings

                use_skills = get_settings().persona_use_skills
            except Exception:
                use_skills = True

        _tutor_agent = build_tutor_agent(use_skills=use_skills)
        from ailine_runtime.tools.registry import build_tool_registry

        register_tools(
            _tutor_agent,
            build_tool_registry(),
            allowed_names=["rag_search"],
        )
    return _tutor_agent


def reset_tutor_agent() -> None:
    """Reset singleton (for testing)."""
    global _tutor_agent
    _tutor_agent = None
