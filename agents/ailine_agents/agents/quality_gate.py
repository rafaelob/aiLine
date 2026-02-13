"""QualityGateAgent — validates study plan drafts (ADR-050 tiered quality gate).

Uses Pydantic AI Agent with output_type=QualityAssessment.
No tools — pure LLM-based assessment combined with deterministic validation.
"""

from __future__ import annotations

import functools

from pydantic_ai import Agent

from ..deps import AgentDeps
from ..models import QualityAssessment
from ._prompts import QUALITY_GATE_SYSTEM_PROMPT


def build_quality_gate_agent() -> Agent[AgentDeps, QualityAssessment]:
    """Create the QualityGateAgent with typed output."""
    agent: Agent[AgentDeps, QualityAssessment] = Agent(
        model="anthropic:claude-sonnet-4-5",
        output_type=QualityAssessment,
        deps_type=AgentDeps,
        system_prompt=QUALITY_GATE_SYSTEM_PROMPT,
        retries=1,
    )
    return agent


@functools.lru_cache(maxsize=1)
def get_quality_gate_agent() -> Agent[AgentDeps, QualityAssessment]:
    """Get or create the singleton QualityGateAgent (cached, thread-safe)."""
    return build_quality_gate_agent()


def reset_quality_gate_agent() -> None:
    """Reset singleton (for testing)."""
    get_quality_gate_agent.cache_clear()
