"""Tests for QualityGateAgent builder and singleton management."""

from __future__ import annotations

from pydantic_ai import Agent

from ailine_agents.agents.quality_gate import (
    build_quality_gate_agent,
    reset_quality_gate_agent,
)
from ailine_agents.deps import AgentDeps
from ailine_agents.models import QualityAssessment


class TestBuildQualityGateAgent:
    """build_quality_gate_agent() produces a correctly configured Agent."""

    def setup_method(self) -> None:
        reset_quality_gate_agent()

    def teardown_method(self) -> None:
        reset_quality_gate_agent()

    def test_returns_agent(self) -> None:
        agent = build_quality_gate_agent()
        assert isinstance(agent, Agent)

    def test_output_type(self) -> None:
        agent = build_quality_gate_agent()
        assert agent._output_type == QualityAssessment

    def test_deps_type(self) -> None:
        agent = build_quality_gate_agent()
        assert agent._deps_type is AgentDeps

    def test_model_name(self) -> None:
        agent = build_quality_gate_agent()
        assert agent.model.model_name == "claude-sonnet-4-5"

    def test_no_tools(self) -> None:
        """QualityGateAgent has no tools -- pure LLM assessment."""
        agent = build_quality_gate_agent()
        assert len(agent._function_toolset.tools) == 0

    def test_retries_configured(self) -> None:
        agent = build_quality_gate_agent()
        assert agent._max_result_retries == 1

    def test_has_system_prompt(self) -> None:
        agent = build_quality_gate_agent()
        assert len(agent._system_prompts) >= 1


class TestResetQualityGateAgent:
    """reset_quality_gate_agent() clears the lru_cache singleton."""

    def test_reset_clears_cache(self) -> None:
        from ailine_agents.agents.quality_gate import get_quality_gate_agent

        # Populate cache
        get_quality_gate_agent()
        assert get_quality_gate_agent.cache_info().currsize == 1

        reset_quality_gate_agent()
        assert get_quality_gate_agent.cache_info().currsize == 0
