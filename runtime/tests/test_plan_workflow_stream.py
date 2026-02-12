"""Tests for the plan workflow re-export shim.

The actual workflow logic is tested in the agents package (ailine_agents).
These tests verify the re-export module works correctly and that
the imported symbols match expectations.
"""

from __future__ import annotations

from ailine_runtime.workflow.plan_workflow import (
    DEFAULT_RECURSION_LIMIT,
    RunState,
    build_plan_workflow,
)


class TestPlanWorkflowReExports:
    """Verify the re-export shim exposes the correct symbols."""

    def test_default_recursion_limit_is_25(self) -> None:
        assert DEFAULT_RECURSION_LIMIT == 25

    def test_run_state_is_type(self) -> None:
        assert RunState is not None

    def test_build_plan_workflow_is_callable(self) -> None:
        assert callable(build_plan_workflow)

    def test_run_state_has_required_keys(self) -> None:
        annotations = RunState.__annotations__
        assert "run_id" in annotations
        assert "user_prompt" in annotations

    def test_imports_come_from_ailine_agents(self) -> None:
        """Ensure re-exports point to ailine_agents, not stale local code."""
        assert build_plan_workflow.__module__.startswith("ailine_agents")
