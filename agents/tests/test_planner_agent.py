"""Tests for PlannerAgent builder and singleton management."""

from __future__ import annotations

from ailine_runtime.domain.entities.plan import StudyPlanDraft
from pydantic_ai import Agent

from ailine_agents.agents.planner import (
    build_planner_agent,
    reset_planner_agent,
)
from ailine_agents.deps import AgentDeps


class TestBuildPlannerAgent:
    """build_planner_agent() produces a correctly configured Agent."""

    def setup_method(self) -> None:
        reset_planner_agent()

    def teardown_method(self) -> None:
        reset_planner_agent()

    def test_returns_agent(self) -> None:
        agent = build_planner_agent()
        assert isinstance(agent, Agent)

    def test_output_type(self) -> None:
        agent = build_planner_agent()
        assert agent._output_type == StudyPlanDraft

    def test_deps_type(self) -> None:
        agent = build_planner_agent()
        assert agent._deps_type is AgentDeps

    def test_model_name(self) -> None:
        agent = build_planner_agent()
        assert agent.model.model_name == "claude-sonnet-4-5"

    def test_has_system_prompt(self) -> None:
        agent = build_planner_agent()
        # At least the static prompt + dynamic prompt function
        assert len(agent._system_prompts) >= 1

    def test_retries_configured(self) -> None:
        agent = build_planner_agent()
        assert agent._max_result_retries == 2


class TestResetPlannerAgent:
    """reset_planner_agent() clears the module-level singleton."""

    def test_reset_clears_singleton(self) -> None:
        from ailine_agents.agents import planner as planner_mod

        # Build via get (creates singleton)
        # We do NOT call get_planner_agent() as it triggers build_tool_registry()
        # Instead just verify the reset mechanism works on the module variable
        planner_mod._planner_agent = build_planner_agent()
        assert planner_mod._planner_agent is not None
        reset_planner_agent()
        assert planner_mod._planner_agent is None
