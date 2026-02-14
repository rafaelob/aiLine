"""Tests for the plan generation LangGraph workflow."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from ailine_agents.deps import AgentDeps
from ailine_agents.workflows._plan_nodes import (
    WorkflowTimeoutError,
    _check_timeout,
    build_executor_prompt,
    build_refinement_feedback,
)
from ailine_agents.workflows.plan_workflow import (
    build_plan_workflow,
    get_idempotency_guard,
)


class TestBuildPlanWorkflow:
    """build_plan_workflow() compiles a LangGraph StateGraph."""

    @patch("ailine_agents.workflows.plan_workflow.get_planner_agent")
    @patch("ailine_agents.workflows.plan_workflow.get_executor_agent")
    def test_compiles_successfully(self, mock_executor: object, mock_planner: object) -> None:
        deps = AgentDeps(teacher_id="t-1", run_id="r-1")
        graph = build_plan_workflow(deps)
        # Compiled graph should have an invoke method
        assert hasattr(graph, "ainvoke")
        assert hasattr(graph, "invoke")

    @patch("ailine_agents.workflows.plan_workflow.get_planner_agent")
    @patch("ailine_agents.workflows.plan_workflow.get_executor_agent")
    def test_graph_has_expected_nodes(self, mock_executor: object, mock_planner: object) -> None:
        deps = AgentDeps(teacher_id="t-1", run_id="r-1")
        graph = build_plan_workflow(deps)
        node_names = set(graph.get_graph().nodes.keys())
        # LangGraph adds __start__ and __end__ nodes
        assert "planner" in node_names
        assert "validate" in node_names
        assert "decision" in node_names
        assert "bump_refine" in node_names
        assert "executor" in node_names


class TestCheckTimeout:
    """_check_timeout() raises WorkflowTimeoutError when time exceeds budget."""

    def test_no_started_at_no_error(self) -> None:
        state = {"run_id": "r-1", "user_prompt": "test"}
        deps = AgentDeps(max_workflow_duration_seconds=300)
        # Should not raise
        _check_timeout(state, deps, "planner")

    def test_within_budget_no_error(self) -> None:
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "started_at": time.monotonic() - 10,  # 10 seconds ago
        }
        deps = AgentDeps(max_workflow_duration_seconds=300)
        _check_timeout(state, deps, "planner")

    def test_exceeds_budget_raises(self) -> None:
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "started_at": time.monotonic() - 400,  # 400 seconds ago
        }
        deps = AgentDeps(max_workflow_duration_seconds=300)
        with pytest.raises(WorkflowTimeoutError, match="timed out"):
            _check_timeout(state, deps, "planner")

    def test_error_message_includes_stage(self) -> None:
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "started_at": time.monotonic() - 600,
        }
        deps = AgentDeps(max_workflow_duration_seconds=300)
        with pytest.raises(WorkflowTimeoutError, match="executor"):
            _check_timeout(state, deps, "executor")


class TestIdempotencyGuard:
    """get_idempotency_guard() returns the module-level guard."""

    def test_returns_guard(self) -> None:
        guard = get_idempotency_guard()
        assert guard is not None
        assert hasattr(guard, "try_acquire")
        assert hasattr(guard, "complete")
        assert hasattr(guard, "fail")


class TestBuildRefinementFeedback:
    """build_refinement_feedback() formats QG feedback for the planner."""

    def test_includes_score(self) -> None:
        prev = {"score": 55, "errors": ["missing steps"], "warnings": ["too long"], "recommendations": ["shorten"]}
        result = build_refinement_feedback(prev, refine_iter=1)
        assert "55" in result
        assert "missing steps" in result
        assert "too long" in result
        assert "shorten" in result

    def test_includes_iteration(self) -> None:
        result = build_refinement_feedback({}, refine_iter=2)
        assert "#2" in result

    def test_empty_prev(self) -> None:
        result = build_refinement_feedback({}, refine_iter=1)
        assert "FEEDBACK DO QUALITY GATE" in result
        assert "None" in result  # score is None

    def test_handles_missing_keys(self) -> None:
        prev = {"score": 70}
        result = build_refinement_feedback(prev, refine_iter=1)
        assert "70" in result
        assert "[]" in result  # empty errors/warnings/recs


class TestBuildExecutorPrompt:
    """build_executor_prompt() formats the executor agent prompt."""

    def test_includes_run_id(self) -> None:
        result = build_executor_prompt(
            draft_json={"title": "Test Plan"},
            run_id="r-42",
            class_profile=None,
            default_variants="standard_html,large_print_html",
        )
        assert "r-42" in result

    def test_includes_variants(self) -> None:
        result = build_executor_prompt(
            draft_json={},
            run_id="r-1",
            class_profile=None,
            default_variants="standard_html,low_distraction_html",
        )
        assert "standard_html" in result
        assert "low_distraction_html" in result

    def test_includes_draft_json(self) -> None:
        result = build_executor_prompt(
            draft_json={"title": "Fractions Lesson"},
            run_id="r-1",
            class_profile=None,
            default_variants="",
        )
        assert "Fractions Lesson" in result

    def test_includes_class_profile(self) -> None:
        profile = {"needs": {"adhd": True}}
        result = build_executor_prompt(
            draft_json={},
            run_id="r-1",
            class_profile=profile,
            default_variants="",
        )
        assert "adhd" in result

    def test_null_class_profile(self) -> None:
        result = build_executor_prompt(
            draft_json={},
            run_id="r-1",
            class_profile=None,
            default_variants="",
        )
        assert "null" in result
