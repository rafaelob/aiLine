"""Tests for ExecutorAgent builder and singleton management."""

from __future__ import annotations

from pydantic_ai import Agent

from ailine_agents.agents.executor import (
    build_executor_agent,
    reset_executor_agent,
)
from ailine_agents.deps import AgentDeps
from ailine_agents.models import ExecutorResult


class TestBuildExecutorAgent:
    """build_executor_agent() produces a correctly configured Agent."""

    def setup_method(self) -> None:
        reset_executor_agent()

    def teardown_method(self) -> None:
        reset_executor_agent()

    def test_returns_agent(self) -> None:
        agent = build_executor_agent()
        assert isinstance(agent, Agent)

    def test_output_type(self) -> None:
        agent = build_executor_agent()
        assert agent._output_type == ExecutorResult

    def test_deps_type(self) -> None:
        agent = build_executor_agent()
        assert agent._deps_type is AgentDeps

    def test_model_name(self) -> None:
        agent = build_executor_agent()
        assert agent.model.model_name == "claude-sonnet-4-5"

    def test_has_system_prompt(self) -> None:
        agent = build_executor_agent()
        assert len(agent._system_prompts) >= 1

    def test_retries_configured(self) -> None:
        agent = build_executor_agent()
        assert agent._max_result_retries == 2


class TestResetExecutorAgent:
    """reset_executor_agent() clears the lru_cache singleton."""

    def test_reset_clears_cache(self) -> None:
        from ailine_agents.agents.executor import _build_and_register_executor

        # Populate cache
        _build_and_register_executor()
        assert _build_and_register_executor.cache_info().currsize == 1

        reset_executor_agent()
        assert _build_and_register_executor.cache_info().currsize == 0
