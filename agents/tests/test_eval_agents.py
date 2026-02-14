"""TestModel-based agent evaluation: 15 golden scenarios + regression detection.

Runs all 5 Planner + 5 QualityGate + 5 Tutor golden scenarios through
pydantic_ai TestModel agents (deterministic, no real API calls).
Each scenario asserts structure and scores via rubric + regression baseline.

ALLOW_MODEL_REQUESTS=False is enforced globally via conftest.py.
"""

from __future__ import annotations

import pytest
from ailine_runtime.domain.entities.plan import StudyPlanDraft
from ailine_runtime.domain.entities.tutor import TutorTurnOutput
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from ailine_agents.deps import AgentDeps
from ailine_agents.eval.golden_sets import (
    PLANNER_GOLDEN,
    QUALITY_GATE_GOLDEN,
    TUTOR_GOLDEN,
)
from ailine_agents.eval.rubric import (
    RubricResult,
    detect_regressions,
    score_planner_output,
    score_quality_gate_output,
    score_tutor_output,
)
from ailine_agents.models import QualityAssessment

# ---------------------------------------------------------------------------
# Baseline scores (locked; regression = drop > 5 points)
# ---------------------------------------------------------------------------

PLANNER_BASELINES: dict[str, float] = {
    "planner-001-fracoes-5ano": 60.0,
    "planner-002-ecossistemas-7ano": 60.0,
    "planner-003-poesia-8ano": 60.0,
    "planner-004-historia-6ano": 60.0,
    "planner-005-geometry-4ano-us": 55.0,
}

QG_BASELINES: dict[str, float] = {
    "qg-001-good-plan": 50.0,
    "qg-002-mediocre-plan": 50.0,
    "qg-003-incomplete-plan": 40.0,
    "qg-004-excellent-plan": 50.0,
    "qg-005-borderline-plan": 50.0,
}

TUTOR_BASELINES: dict[str, float] = {
    "tutor-001-fracoes-basicas": 55.0,
    "tutor-002-misconception": 55.0,
    "tutor-003-offtopic": 50.0,
    "tutor-004-clarification": 50.0,
    "tutor-005-greeting": 50.0,
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def planner_agent() -> Agent[AgentDeps, StudyPlanDraft]:
    """Planner agent with TestModel (no real API calls)."""
    return Agent(
        model=TestModel(),
        output_type=StudyPlanDraft,
        deps_type=AgentDeps,
        system_prompt="You are a lesson planner.",
    )


@pytest.fixture()
def qg_agent() -> Agent[AgentDeps, QualityAssessment]:
    """QualityGate agent with TestModel."""
    return Agent(
        model=TestModel(),
        output_type=QualityAssessment,
        deps_type=AgentDeps,
        system_prompt="You are a quality gate.",
    )


@pytest.fixture()
def tutor_agent() -> Agent[AgentDeps, TutorTurnOutput]:
    """Tutor agent with TestModel."""
    return Agent(
        model=TestModel(),
        output_type=TutorTurnOutput,
        deps_type=AgentDeps,
        system_prompt="You are a Socratic tutor.",
    )


@pytest.fixture()
def eval_deps() -> AgentDeps:
    return AgentDeps(
        teacher_id="eval-teacher", run_id="eval-run", subject="matematica"
    )


# ---------------------------------------------------------------------------
# Helper: run regression check
# ---------------------------------------------------------------------------


def _check_no_regressions(
    current: list[RubricResult],
    baselines: dict[str, float],
    agent_type: str,
) -> None:
    baseline_results = [
        RubricResult(
            agent_type=agent_type,
            scenario_id=r.scenario_id,
            dimensions=(),
            final_score=baselines.get(r.scenario_id, 45.0),
            passed=True,
        )
        for r in current
    ]
    reports = detect_regressions(current, baseline_results, tolerance=5.0)
    regressions = [r for r in reports if r.regressed]
    assert not regressions, (
        f"{agent_type} regressions: "
        f"{[(r.scenario_id, r.current_score, r.baseline_score) for r in regressions]}"
    )


# ---------------------------------------------------------------------------
# Planner agent eval (5 scenarios)
# ---------------------------------------------------------------------------


class TestPlannerAgentEval:
    """Run all 5 Planner golden scenarios through TestModel agent."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scenario", PLANNER_GOLDEN, ids=[s["id"] for s in PLANNER_GOLDEN]
    )
    async def test_scenario(self, planner_agent, eval_deps, scenario) -> None:
        result = await planner_agent.run(scenario["prompt"], deps=eval_deps)
        output = result.output
        assert isinstance(output, StudyPlanDraft)
        assert output.title
        assert output.objectives
        assert output.steps

        rubric = score_planner_output(output, scenario)
        assert rubric.agent_type == "planner"
        assert rubric.scenario_id == scenario["id"]
        assert rubric.final_score > 0

    @pytest.mark.asyncio
    async def test_regression(self, planner_agent, eval_deps) -> None:
        results = []
        for s in PLANNER_GOLDEN:
            r = await planner_agent.run(s["prompt"], deps=eval_deps)
            results.append(score_planner_output(r.output, s))
        _check_no_regressions(results, PLANNER_BASELINES, "planner")


# ---------------------------------------------------------------------------
# QualityGate agent eval (5 scenarios)
# ---------------------------------------------------------------------------


class TestQualityGateAgentEval:
    """Run all 5 QualityGate golden scenarios through TestModel agent."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scenario", QUALITY_GATE_GOLDEN, ids=[s["id"] for s in QUALITY_GATE_GOLDEN]
    )
    async def test_scenario(self, qg_agent, eval_deps, scenario) -> None:
        result = await qg_agent.run(scenario["prompt"], deps=eval_deps)
        output = result.output
        assert isinstance(output, QualityAssessment)
        assert 0 <= output.score <= 100
        assert isinstance(output.status, str) and len(output.status) > 0

        rubric = score_quality_gate_output(output, scenario)
        assert rubric.agent_type == "quality_gate"
        assert rubric.final_score > 0

    @pytest.mark.asyncio
    async def test_regression(self, qg_agent, eval_deps) -> None:
        results = []
        for s in QUALITY_GATE_GOLDEN:
            r = await qg_agent.run(s["prompt"], deps=eval_deps)
            results.append(score_quality_gate_output(r.output, s))
        _check_no_regressions(results, QG_BASELINES, "quality_gate")


# ---------------------------------------------------------------------------
# Tutor agent eval (5 scenarios)
# ---------------------------------------------------------------------------


class TestTutorAgentEval:
    """Run all 5 Tutor golden scenarios through TestModel agent."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "scenario", TUTOR_GOLDEN, ids=[s["id"] for s in TUTOR_GOLDEN]
    )
    async def test_scenario(self, tutor_agent, eval_deps, scenario) -> None:
        result = await tutor_agent.run(scenario["prompt"], deps=eval_deps)
        output = result.output
        assert isinstance(output, TutorTurnOutput)
        assert output.answer_markdown is not None

        rubric = score_tutor_output(output, scenario)
        assert rubric.agent_type == "tutor"
        assert rubric.final_score > 0

    @pytest.mark.asyncio
    async def test_regression(self, tutor_agent, eval_deps) -> None:
        results = []
        for s in TUTOR_GOLDEN:
            r = await tutor_agent.run(s["prompt"], deps=eval_deps)
            results.append(score_tutor_output(r.output, s))
        _check_no_regressions(results, TUTOR_BASELINES, "tutor")
