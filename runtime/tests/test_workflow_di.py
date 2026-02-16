"""Tests for workflow DI via AgentDeps.

Verifies that build_plan_workflow accepts AgentDeps and produces
a compiled graph (FINDING-02: port-based DI, now via Pydantic AI).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ailine_agents import AgentDeps

from ailine_runtime.workflow.plan_workflow import build_plan_workflow


def _mock_agent():
    """Create a mock Pydantic AI Agent for testing."""
    mock = MagicMock()
    mock.name = "mock-agent"
    return mock


class TestWorkflowDI:
    def test_build_with_agent_deps(self) -> None:
        """build_plan_workflow accepts AgentDeps and returns a compiled graph."""
        deps = AgentDeps(
            teacher_id="teacher-001",
            run_id="test-run",
            max_refinement_iters=0,
            default_variants="standard_html",
        )
        with (
            patch(
                "ailine_agents.workflows.plan_workflow.get_planner_agent",
                return_value=_mock_agent(),
            ),
            patch(
                "ailine_agents.workflows.plan_workflow.get_executor_agent",
                return_value=_mock_agent(),
            ),
        ):
            graph = build_plan_workflow(deps)
        assert graph is not None

    def test_build_with_minimal_deps(self) -> None:
        """build_plan_workflow works with minimal AgentDeps."""
        deps = AgentDeps()
        with (
            patch(
                "ailine_agents.workflows.plan_workflow.get_planner_agent",
                return_value=_mock_agent(),
            ),
            patch(
                "ailine_agents.workflows.plan_workflow.get_executor_agent",
                return_value=_mock_agent(),
            ),
        ):
            graph = build_plan_workflow(deps)
        assert graph is not None
