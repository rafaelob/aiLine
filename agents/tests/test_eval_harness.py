"""Agent evaluation harness tests.

Tests rubric scoring, golden set validation, regression detection,
and EvalRubric heuristic scorers (no real LLM calls).

TestModel-based agent execution tests are in test_eval_agents.py.
"""

from __future__ import annotations

import pytest
from ailine_runtime.domain.entities.plan import (
    AccessibilityPackDraft,
    Objective,
    PlanStep,
    StudyPlanDraft,
)
from ailine_runtime.domain.entities.tutor import TutorTurnOutput

from ailine_agents.eval import (
    EvalRubric,
    score_plan_output,
    score_tutor_response,
)
from ailine_agents.eval.golden_sets import (
    PLANNER_GOLDEN,
    QUALITY_GATE_GOLDEN,
    TUTOR_GOLDEN,
)
from ailine_agents.eval.rubric import (
    RegressionReport,
    RubricDimension,
    RubricResult,
    compute_rubric_score,
    detect_regressions,
    score_planner_output,
    score_quality_gate_output,
    score_tutor_output,
)
from ailine_agents.models import QualityAssessment

# ---------------------------------------------------------------------------
# Rubric scoring unit tests
# ---------------------------------------------------------------------------


class TestComputeRubricScore:
    def test_empty_dimensions(self) -> None:
        assert compute_rubric_score([]) == 0.0

    def test_single_dimension(self) -> None:
        dims = [RubricDimension("test", 80, weight=1.0)]
        assert compute_rubric_score(dims) == 80.0

    def test_weighted_average(self) -> None:
        dims = [
            RubricDimension("a", 100, weight=0.6),
            RubricDimension("b", 50, weight=0.4),
        ]
        # (100*0.6 + 50*0.4) / (0.6+0.4) = 80.0
        assert compute_rubric_score(dims) == 80.0

    def test_zero_weight(self) -> None:
        dims = [RubricDimension("x", 100, weight=0.0)]
        assert compute_rubric_score(dims) == 0.0


# ---------------------------------------------------------------------------
# Planner rubric tests
# ---------------------------------------------------------------------------


def _make_good_plan() -> StudyPlanDraft:
    return StudyPlanDraft(
        title="Fracoes para 5o ano",
        grade="5o ano",
        standard="BNCC",
        objectives=[
            Objective(id="EF05MA03", text="Comparar e ordenar fracoes"),
        ],
        steps=[
            PlanStep(minutes=15, title="Introducao", instructions=["Explicar conceito"]),
            PlanStep(minutes=20, title="Atividade", instructions=["Praticar em duplas"]),
            PlanStep(minutes=10, title="Avaliacao", instructions=["Quiz formativo"]),
        ],
        accessibility_pack_draft=AccessibilityPackDraft(
            applied_adaptations=[],
        ),
    )


def _make_empty_plan() -> StudyPlanDraft:
    return StudyPlanDraft(
        title="",
        grade="",
        standard="",
        objectives=[],
        steps=[],
    )


class TestPlannerRubric:
    def test_good_plan_passes(self) -> None:
        plan = _make_good_plan()
        result = score_planner_output(plan, PLANNER_GOLDEN[0])
        assert result.passed
        assert result.final_score >= 70
        assert result.agent_type == "planner"
        assert result.scenario_id == "planner-001-fracoes-5ano"

    def test_empty_plan_fails(self) -> None:
        plan = _make_empty_plan()
        result = score_planner_output(plan, PLANNER_GOLDEN[0])
        assert not result.passed
        assert result.final_score < 70

    def test_all_dimensions_present(self) -> None:
        plan = _make_good_plan()
        result = score_planner_output(plan, PLANNER_GOLDEN[0])
        dim_names = {d.name for d in result.dimensions}
        assert dim_names == {"structure", "completeness", "pedagogy", "safety", "accuracy"}

    def test_dimension_dict(self) -> None:
        plan = _make_good_plan()
        result = score_planner_output(plan, PLANNER_GOLDEN[0])
        dd = result.dimension_dict
        assert "structure" in dd
        assert 0 <= dd["structure"] <= 100

    @pytest.mark.parametrize("scenario", PLANNER_GOLDEN, ids=[s["id"] for s in PLANNER_GOLDEN])
    def test_golden_scenarios_have_valid_config(self, scenario: dict) -> None:
        """Each golden scenario has required fields."""
        assert "id" in scenario
        assert "prompt" in scenario
        assert "expected_grade" in scenario
        assert "threshold" in scenario


# ---------------------------------------------------------------------------
# QualityGate rubric tests
# ---------------------------------------------------------------------------


def _make_good_assessment() -> QualityAssessment:
    return QualityAssessment(
        score=85,
        status="accept",
        errors=[],
        warnings=[],
        recommendations=["Considere adicionar mais exemplos praticos"],
        checklist={"objectives_clear": True, "timing_adequate": True},
    )


def _make_poor_assessment() -> QualityAssessment:
    return QualityAssessment(
        score=35,
        status="must-refine",
        errors=["Sem objetivos claros"],
        warnings=["Tempo de aula muito curto"],
        recommendations=["Reescrever objetivos", "Adicionar adaptacoes"],
        checklist={"objectives_clear": False, "timing_adequate": False},
    )


class TestQualityGateRubric:
    def test_good_assessment_scores_high(self) -> None:
        qa = _make_good_assessment()
        result = score_quality_gate_output(qa, QUALITY_GATE_GOLDEN[0])
        assert result.final_score >= 70
        assert result.agent_type == "quality_gate"

    def test_poor_assessment_with_matching_status(self) -> None:
        qa = _make_poor_assessment()
        result = score_quality_gate_output(qa, QUALITY_GATE_GOLDEN[1])
        # Poor plan with must-refine status should score OK against must-refine expectation
        assert result.final_score >= 50

    def test_mismatched_status_penalized(self) -> None:
        qa = _make_good_assessment()  # score=85, status="accept"
        # Test against scenario expecting must-refine
        result = score_quality_gate_output(qa, QUALITY_GATE_GOLDEN[2])
        # Score is out of expected range and status mismatches
        assert result.final_score < 80

    @pytest.mark.parametrize("scenario", QUALITY_GATE_GOLDEN, ids=[s["id"] for s in QUALITY_GATE_GOLDEN])
    def test_golden_scenarios_have_valid_config(self, scenario: dict) -> None:
        assert "id" in scenario
        assert "prompt" in scenario
        assert "expected_score_range" in scenario
        assert "expected_status" in scenario


# ---------------------------------------------------------------------------
# Tutor rubric tests
# ---------------------------------------------------------------------------


def _make_socratic_response() -> TutorTurnOutput:
    return TutorTurnOutput(
        answer_markdown=(
            "Boa pergunta! Vamos pensar juntos sobre fracoes. "
            "Quando voce divide algo em partes iguais, cada parte e uma fracao. "
            "Se voce tem uma pizza e corta ao meio, cada parte e 1/2. "
            "Consegue pensar em outro exemplo de metade?"
        ),
        step_by_step=["1. Pense em algo inteiro", "2. Divida em partes iguais"],
        check_for_understanding=["O que acontece se dividir em 4 partes?"],
        options_to_respond=["Sim, entendi!", "Pode explicar mais?"],
        citations=[],
    )


def _make_direct_answer() -> TutorTurnOutput:
    return TutorTurnOutput(
        answer_markdown="1/2 e 0.5. Pronto.",
        step_by_step=[],
        check_for_understanding=[],
        options_to_respond=[],
        citations=[],
    )


class TestTutorRubric:
    def test_socratic_response_scores_high(self) -> None:
        output = _make_socratic_response()
        result = score_tutor_output(output, TUTOR_GOLDEN[0])
        assert result.final_score >= 65
        assert result.agent_type == "tutor"

    def test_direct_answer_scores_lower(self) -> None:
        """A direct non-Socratic answer should score lower on pedagogy."""
        output = _make_direct_answer()
        result = score_tutor_output(output, TUTOR_GOLDEN[0])
        # Still has structure but poor pedagogy
        socratic_result = score_tutor_output(_make_socratic_response(), TUTOR_GOLDEN[0])
        assert result.final_score < socratic_result.final_score

    def test_empty_answer_fails(self) -> None:
        output = TutorTurnOutput(
            answer_markdown="",
            step_by_step=[],
            check_for_understanding=[],
            options_to_respond=[],
            citations=[],
        )
        result = score_tutor_output(output, TUTOR_GOLDEN[0])
        assert not result.passed

    @pytest.mark.parametrize("scenario", TUTOR_GOLDEN, ids=[s["id"] for s in TUTOR_GOLDEN])
    def test_golden_scenarios_have_valid_config(self, scenario: dict) -> None:
        assert "id" in scenario
        assert "prompt" in scenario
        assert "expected_keywords" in scenario


# ---------------------------------------------------------------------------
# Regression detection tests
# ---------------------------------------------------------------------------


class TestRegressionDetection:
    def test_no_regression_when_scores_stable(self) -> None:
        baseline = [
            RubricResult("planner", "s1", (), 80.0, True),
            RubricResult("planner", "s2", (), 75.0, True),
        ]
        current = [
            RubricResult("planner", "s1", (), 82.0, True),
            RubricResult("planner", "s2", (), 74.0, True),
        ]
        reports = detect_regressions(current, baseline)
        assert len(reports) == 2
        assert not any(r.regressed for r in reports)

    def test_regression_detected(self) -> None:
        baseline = [RubricResult("planner", "s1", (), 80.0, True)]
        current = [RubricResult("planner", "s1", (), 60.0, False)]
        reports = detect_regressions(current, baseline)
        assert len(reports) == 1
        assert reports[0].regressed
        assert reports[0].delta == -20.0

    def test_improvement_detected(self) -> None:
        baseline = [RubricResult("planner", "s1", (), 60.0, False)]
        current = [RubricResult("planner", "s1", (), 80.0, True)]
        reports = detect_regressions(current, baseline)
        assert len(reports) == 1
        assert reports[0].improved
        assert not reports[0].regressed

    def test_tolerance_respected(self) -> None:
        baseline = [RubricResult("planner", "s1", (), 80.0, True)]
        current = [RubricResult("planner", "s1", (), 76.0, True)]
        # Default tolerance is 5, drop of 4 is within tolerance
        reports = detect_regressions(current, baseline, tolerance=5.0)
        assert not reports[0].regressed

    def test_new_scenarios_ignored(self) -> None:
        baseline = [RubricResult("planner", "s1", (), 80.0, True)]
        current = [
            RubricResult("planner", "s1", (), 80.0, True),
            RubricResult("planner", "s2-new", (), 90.0, True),
        ]
        reports = detect_regressions(current, baseline)
        # Only s1 has a baseline comparison
        assert len(reports) == 1

    def test_report_fields(self) -> None:
        report = RegressionReport(
            scenario_id="test",
            agent_type="planner",
            current_score=90.0,
            baseline_score=80.0,
            delta=10.0,
            regressed=False,
        )
        assert report.improved  # delta=10 > tolerance=5
        assert not report.regressed


# ---------------------------------------------------------------------------
# Golden set completeness
# ---------------------------------------------------------------------------


class TestGoldenSetCompleteness:
    def test_planner_has_5_scenarios(self) -> None:
        assert len(PLANNER_GOLDEN) == 5

    def test_quality_gate_has_5_scenarios(self) -> None:
        assert len(QUALITY_GATE_GOLDEN) == 5

    def test_tutor_has_5_scenarios(self) -> None:
        assert len(TUTOR_GOLDEN) == 5

    def test_all_ids_unique(self) -> None:
        all_ids = (
            [s["id"] for s in PLANNER_GOLDEN] + [s["id"] for s in QUALITY_GATE_GOLDEN] + [s["id"] for s in TUTOR_GOLDEN]
        )
        assert len(all_ids) == len(set(all_ids))


# ---------------------------------------------------------------------------
# EvalRubric heuristic scorer tests
# ---------------------------------------------------------------------------


class TestEvalRubricScoring:
    """Tests for the lightweight EvalRubric heuristic scorers."""

    def test_score_plan_output_rich_text(self) -> None:
        plan_text = (
            "# Plano de Aula: Fracoes\n\n"
            "## Objetivo\n"
            "- EF05MA03: Comparar e ordenar fracoes (BNCC)\n\n"
            "## Materiais\n"
            "- Material concreto\n\n"
            "## Atividades\n"
            "1. Introducao com material concreto (15 min)\n"
            "2. Atividade em duplas (20 min)\n"
            "3. Avaliacao formativa (10 min)\n\n"
            "## Avaliacao\n"
            "Quiz sobre comparacao de fracoes.\n\n"
            "Adaptacoes de acessibilidade inclusivas para diversidade."
        )
        rubric = score_plan_output(plan_text)
        assert isinstance(rubric, EvalRubric)
        assert rubric.structure >= 70
        assert rubric.accuracy >= 60
        assert rubric.safety >= 60
        assert rubric.pedagogy >= 40
        assert rubric.average > 50

    def test_score_plan_output_minimal_text(self) -> None:
        rubric = score_plan_output("Aula de matematica.")
        assert rubric.structure <= 70
        assert rubric.accuracy <= 50

    def test_score_tutor_response_socratic(self) -> None:
        response = (
            "Que otima pergunta! Pense assim: se voce tem uma pizza "
            "inteira e divide em 2 partes iguais, cada parte e que fracao?\n"
            "Tente imaginar! Por que voce acha que 1/2 significa metade?"
        )
        rubric = score_tutor_response(response, context="fracoes basicas")
        assert isinstance(rubric, EvalRubric)
        assert rubric.pedagogy >= 50
        assert rubric.average > 40

    def test_score_tutor_response_short(self) -> None:
        rubric = score_tutor_response("1/2 e metade.")
        assert rubric.pedagogy <= 70
        assert rubric.structure <= 70

    def test_eval_rubric_average(self) -> None:
        rubric = EvalRubric(accuracy=80, safety=90, pedagogy=70, structure=60)
        assert rubric.average == 75.0
