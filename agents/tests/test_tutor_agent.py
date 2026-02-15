"""Tests for TutorAgent builder and singleton management."""

from __future__ import annotations

from ailine_runtime.domain.entities.tutor import TutorTurnOutput
from pydantic_ai import Agent
from pydantic_ai.models import Model

from ailine_agents.agents.tutor import (
    build_tutor_agent,
    reset_tutor_agent,
)
from ailine_agents.deps import AgentDeps


class TestBuildTutorAgent:
    """build_tutor_agent() produces a correctly configured Agent."""

    def setup_method(self) -> None:
        reset_tutor_agent()

    def teardown_method(self) -> None:
        reset_tutor_agent()

    def test_returns_agent(self) -> None:
        agent = build_tutor_agent()
        assert isinstance(agent, Agent)

    def test_output_type(self) -> None:
        agent = build_tutor_agent()
        assert agent._output_type == TutorTurnOutput

    def test_deps_type(self) -> None:
        agent = build_tutor_agent()
        assert agent._deps_type is AgentDeps

    def test_model_name(self) -> None:
        agent = build_tutor_agent()
        assert isinstance(agent.model, Model)
        assert agent.model.model_name == "claude-sonnet-4-5"

    def test_has_system_prompt(self) -> None:
        agent = build_tutor_agent()
        assert len(agent._system_prompts) >= 1

    def test_retries_configured(self) -> None:
        agent = build_tutor_agent()
        assert agent._max_result_retries == 2


class TestResetTutorAgent:
    """reset_tutor_agent() clears the lru_cache singletons."""

    def test_reset_clears_cache(self) -> None:
        from ailine_agents.agents.tutor import _build_and_register_tutor

        # Populate cache
        _build_and_register_tutor(True)
        assert _build_and_register_tutor.cache_info().currsize == 1

        reset_tutor_agent()
        assert _build_and_register_tutor.cache_info().currsize == 0
