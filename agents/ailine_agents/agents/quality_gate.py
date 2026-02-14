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

_DEFAULT_QG_MODEL = "anthropic:claude-sonnet-4-5"


def build_quality_gate_agent(*, model: str | None = None) -> Agent[AgentDeps, QualityAssessment]:
    """Create the QualityGateAgent with typed output.

    Args:
        model: Override the default model ID (e.g. for testing or SmartRouter).
    """
    agent: Agent[AgentDeps, QualityAssessment] = Agent(
        model=model or _DEFAULT_QG_MODEL,
        output_type=QualityAssessment,
        deps_type=AgentDeps,
        system_prompt=QUALITY_GATE_SYSTEM_PROMPT,
        retries=1,
    )
    return agent


@functools.lru_cache(maxsize=4)
def _build_and_cache_qg(model: str | None = None) -> Agent[AgentDeps, QualityAssessment]:
    """Build quality gate agent (cached, thread-safe via lru_cache)."""
    return build_quality_gate_agent(model=model)


def get_quality_gate_agent(*, model: str | None = None) -> Agent[AgentDeps, QualityAssessment]:
    """Get or create the singleton QualityGateAgent."""
    if model is None:
        try:
            from ailine_runtime.shared.config import get_settings

            model = getattr(get_settings(), "qg_model", None)
        except (ImportError, AttributeError):
            pass

    return _build_and_cache_qg(model)


def reset_quality_gate_agent() -> None:
    """Reset singleton (for testing)."""
    _build_and_cache_qg.cache_clear()
