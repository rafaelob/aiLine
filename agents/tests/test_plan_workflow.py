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
    quality_gate_route,
)


class TestBuildPlanWorkflow:
    """build_plan_workflow() compiles a LangGraph StateGraph."""

    @patch("ailine_agents.workflows.plan_workflow.get_planner_agent")
    @patch("ailine_agents.workflows.plan_workflow.get_executor_agent")
    def test_compiles_successfully(
        self, mock_executor: object, mock_planner: object
    ) -> None:
        deps = AgentDeps(teacher_id="t-1", run_id="r-1")
        graph = build_plan_workflow(deps)
        # Compiled graph should have an invoke method
        assert hasattr(graph, "ainvoke")
        assert hasattr(graph, "invoke")

    @patch("ailine_agents.workflows.plan_workflow.get_planner_agent")
    @patch("ailine_agents.workflows.plan_workflow.get_executor_agent")
    def test_graph_has_expected_nodes(
        self, mock_executor: object, mock_planner: object
    ) -> None:
        deps = AgentDeps(teacher_id="t-1", run_id="r-1")
        graph = build_plan_workflow(deps)
        node_names = set(graph.get_graph().nodes.keys())
        # LangGraph adds __start__ and __end__ nodes
        assert "skills" in node_names
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
        # Should not raise -- minimal dict intentionally used in tests
        _check_timeout(state, deps, "planner")  # type: ignore[arg-type]

    def test_within_budget_no_error(self) -> None:
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "started_at": time.monotonic() - 10,  # 10 seconds ago
        }
        deps = AgentDeps(max_workflow_duration_seconds=300)
        _check_timeout(state, deps, "planner")  # type: ignore[arg-type]

    def test_exceeds_budget_raises(self) -> None:
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "started_at": time.monotonic() - 400,  # 400 seconds ago
        }
        deps = AgentDeps(max_workflow_duration_seconds=300)
        with pytest.raises(WorkflowTimeoutError, match="timed out"):
            _check_timeout(state, deps, "planner")  # type: ignore[arg-type]

    def test_error_message_includes_stage(self) -> None:
        state = {
            "run_id": "r-1",
            "user_prompt": "test",
            "started_at": time.monotonic() - 600,
        }
        deps = AgentDeps(max_workflow_duration_seconds=300)
        with pytest.raises(WorkflowTimeoutError, match="executor"):
            _check_timeout(state, deps, "executor")  # type: ignore[arg-type]


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
        prev = {
            "score": 55,
            "errors": ["missing steps"],
            "warnings": ["too long"],
            "recommendations": ["shorten"],
        }
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
        assert "QUALITY GATE FEEDBACK" in result
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


class TestQualityGateRouting:
    """Tests for quality_gate_route() tiered routing (ADR-050).

    Tiers:
    - <60: reject -- MUST refine (if budget remains)
    - 60-79: marginal -- refine if budget, else execute
    - >=80: accept -- proceed to execution
    """

    def test_high_score_executes(self) -> None:
        """Score >= 80 always routes to execute."""
        assert quality_gate_route(85, refine_iter=0, max_iters=3) == "execute"
        assert quality_gate_route(100, refine_iter=0, max_iters=3) == "execute"
        assert quality_gate_route(95, refine_iter=2, max_iters=3) == "execute"

    def test_high_score_executes_even_without_budget(self) -> None:
        """Score >= 80 routes to execute even when budget exhausted."""
        assert quality_gate_route(80, refine_iter=3, max_iters=3) == "execute"

    def test_low_score_with_budget_refines(self) -> None:
        """Score < 60 with budget routes to refine."""
        assert quality_gate_route(45, refine_iter=0, max_iters=3) == "refine"
        assert quality_gate_route(0, refine_iter=1, max_iters=3) == "refine"
        assert quality_gate_route(59, refine_iter=2, max_iters=3) == "refine"

    def test_low_score_no_budget_executes(self) -> None:
        """Score < 60 without budget routes to execute (best effort)."""
        assert quality_gate_route(40, refine_iter=3, max_iters=3) == "execute"
        assert quality_gate_route(0, refine_iter=5, max_iters=3) == "execute"

    def test_marginal_score_with_budget_refines(self) -> None:
        """Score 60-79 with budget routes to refine."""
        assert quality_gate_route(60, refine_iter=0, max_iters=3) == "refine"
        assert quality_gate_route(70, refine_iter=1, max_iters=3) == "refine"
        assert quality_gate_route(79, refine_iter=2, max_iters=3) == "refine"

    def test_marginal_score_no_budget_executes(self) -> None:
        """Score 60-79 without budget routes to execute."""
        assert quality_gate_route(72, refine_iter=3, max_iters=3) == "execute"
        assert quality_gate_route(60, refine_iter=3, max_iters=3) == "execute"

    def test_boundary_score_80(self) -> None:
        """Score exactly 80 routes to execute (boundary of accept tier)."""
        assert quality_gate_route(80, refine_iter=0, max_iters=3) == "execute"

    def test_boundary_score_60(self) -> None:
        """Score exactly 60 is marginal tier, not reject tier."""
        assert quality_gate_route(60, refine_iter=0, max_iters=3) == "refine"
        assert quality_gate_route(60, refine_iter=3, max_iters=3) == "execute"

    def test_boundary_score_59(self) -> None:
        """Score 59 is reject tier."""
        assert quality_gate_route(59, refine_iter=0, max_iters=3) == "refine"
        assert quality_gate_route(59, refine_iter=3, max_iters=3) == "execute"

    def test_zero_max_iters(self) -> None:
        """With max_iters=0, no budget is ever available."""
        assert quality_gate_route(50, refine_iter=0, max_iters=0) == "execute"
        assert quality_gate_route(70, refine_iter=0, max_iters=0) == "execute"
        assert quality_gate_route(90, refine_iter=0, max_iters=0) == "execute"
