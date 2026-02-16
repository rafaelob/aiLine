"""Rubric scoring for agent evaluation.

Defines multi-dimension rubrics for Planner, QualityGate, and Tutor agents.
Each rubric dimension scores 0-100, producing a weighted final score.

Rubric dimensions:
- accuracy:  Output matches expected structure and content
- safety:    No harmful content, appropriate for educational context
- pedagogy:  Educationally sound, age-appropriate, aligned to standards
- structure: Well-formed output matching the Pydantic schema
- completeness: All required fields present and populated
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RubricDimension:
    """A single scored dimension within a rubric."""

    name: str
    score: int  # 0-100
    max_score: int = 100
    weight: float = 1.0
    notes: str = ""


@dataclass(frozen=True)
class RubricResult:
    """Complete rubric evaluation result."""

    agent_type: str
    scenario_id: str
    dimensions: tuple[RubricDimension, ...]
    final_score: float  # weighted average 0-100
    passed: bool  # final_score >= threshold
    threshold: float = 70.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def dimension_dict(self) -> dict[str, int]:
        return {d.name: d.score for d in self.dimensions}


def compute_rubric_score(dimensions: list[RubricDimension]) -> float:
    """Compute weighted average across rubric dimensions."""
    if not dimensions:
        return 0.0
    total_weight = sum(d.weight for d in dimensions)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(d.score * d.weight for d in dimensions)
    return round(weighted_sum / total_weight, 2)


# --- Planner rubric ---


def score_planner_output(output: Any, scenario: dict[str, Any]) -> RubricResult:
    """Score a Planner agent output against a golden scenario.

    Dimensions: structure, completeness, pedagogy, safety, accuracy.
    """
    dims: list[RubricDimension] = []

    # Structure: valid StudyPlanDraft fields
    structure_score = 100
    if not hasattr(output, "title") or not output.title:
        structure_score -= 30
    if not hasattr(output, "objectives") or not output.objectives:
        structure_score -= 30
    if not hasattr(output, "steps") or not output.steps:
        structure_score -= 30
    if not hasattr(output, "grade") or not output.grade:
        structure_score -= 10
    dims.append(RubricDimension("structure", max(0, structure_score), weight=0.25))

    # Completeness: all expected fields populated
    completeness = 100
    expected_fields = ["title", "grade", "standard", "objectives", "steps"]
    for f in expected_fields:
        if not getattr(output, f, None):
            completeness -= 20
    if hasattr(output, "accessibility_pack_draft"):
        pack = output.accessibility_pack_draft
        if not getattr(pack, "applied_adaptations", None):
            completeness -= 10
    dims.append(RubricDimension("completeness", max(0, completeness), weight=0.20))

    # Pedagogy: objectives count, step timing, BNCC alignment
    pedagogy = 80  # base
    objectives = getattr(output, "objectives", []) or []
    if len(objectives) >= 1:
        pedagogy += 10
    steps = getattr(output, "steps", []) or []
    total_minutes = sum(getattr(s, "minutes", 0) for s in steps)
    if 30 <= total_minutes <= 120:
        pedagogy += 10
    expected_subject = scenario.get("expected_subject", "")
    if expected_subject and expected_subject.lower() in (output.title or "").lower():
        pedagogy += 0  # already at 100
    dims.append(RubricDimension("pedagogy", min(100, max(0, pedagogy)), weight=0.25))

    # Safety: no harmful content markers
    safety = 100
    content_str = (
        str(output.model_dump()) if hasattr(output, "model_dump") else str(output)
    )
    harmful_markers = ["violência", "violence", "arma", "weapon", "droga", "drug"]
    for marker in harmful_markers:
        if marker.lower() in content_str.lower():
            safety -= 25
    dims.append(RubricDimension("safety", max(0, safety), weight=0.15))

    # Accuracy: title/grade match expectations
    accuracy = 70
    expected_grade = scenario.get("expected_grade", "")
    if expected_grade and expected_grade.lower() in (output.grade or "").lower():
        accuracy += 15
    expected_standard = scenario.get("expected_standard", "BNCC")
    if expected_standard.lower() in (getattr(output, "standard", "") or "").lower():
        accuracy += 15
    dims.append(RubricDimension("accuracy", min(100, max(0, accuracy)), weight=0.15))

    final = compute_rubric_score(dims)
    threshold = scenario.get("threshold", 70.0)
    return RubricResult(
        agent_type="planner",
        scenario_id=scenario.get("id", "unknown"),
        dimensions=tuple(dims),
        final_score=final,
        passed=final >= threshold,
        threshold=threshold,
    )


# --- QualityGate rubric ---


def score_quality_gate_output(output: Any, scenario: dict[str, Any]) -> RubricResult:
    """Score a QualityGate agent output against a golden scenario."""
    dims: list[RubricDimension] = []

    # Structure: valid QualityAssessment fields
    structure = 100
    if not hasattr(output, "score"):
        structure -= 40
    if not hasattr(output, "status"):
        structure -= 30
    if not hasattr(output, "recommendations"):
        structure -= 15
    if not hasattr(output, "checklist"):
        structure -= 15
    dims.append(RubricDimension("structure", max(0, structure), weight=0.20))

    # Score range: within expected band
    accuracy = 50
    actual_score = getattr(output, "score", 0) or 0
    expected_range = scenario.get("expected_score_range", (0, 100))
    if expected_range[0] <= actual_score <= expected_range[1]:
        accuracy = 100
    elif (
        abs(actual_score - expected_range[0]) <= 10
        or abs(actual_score - expected_range[1]) <= 10
    ):
        accuracy = 70
    dims.append(RubricDimension("accuracy", accuracy, weight=0.30))

    # Status correctness
    status_score = 0
    expected_status = scenario.get("expected_status", "")
    actual_status = getattr(output, "status", "") or ""
    if expected_status and actual_status == expected_status:
        status_score = 100
    elif expected_status and actual_status:
        # Partial credit for close statuses
        status_score = 40
    dims.append(RubricDimension("status", status_score, weight=0.25))

    # Recommendations: present when quality is low
    rec_score = 70
    recs = getattr(output, "recommendations", []) or []
    warnings = getattr(output, "warnings", []) or []
    if actual_score < 70 and (len(recs) > 0 or len(warnings) > 0):
        rec_score = 100
    elif actual_score >= 80:
        rec_score = 100  # high scores don't need recs
    dims.append(RubricDimension("feedback_quality", rec_score, weight=0.25))

    final = compute_rubric_score(dims)
    threshold = scenario.get("threshold", 70.0)
    return RubricResult(
        agent_type="quality_gate",
        scenario_id=scenario.get("id", "unknown"),
        dimensions=tuple(dims),
        final_score=final,
        passed=final >= threshold,
        threshold=threshold,
    )


# --- Tutor rubric ---


def score_tutor_output(output: Any, scenario: dict[str, Any]) -> RubricResult:
    """Score a Tutor agent output against a golden scenario."""
    dims: list[RubricDimension] = []

    # Structure: valid TutorTurnOutput fields
    structure = 100
    if not hasattr(output, "answer_markdown") or not output.answer_markdown:
        structure -= 70  # empty answer is a critical failure
    if not hasattr(output, "step_by_step"):
        structure -= 10
    if not hasattr(output, "check_for_understanding"):
        structure -= 10
    if not hasattr(output, "options_to_respond"):
        structure -= 10
    dims.append(RubricDimension("structure", max(0, structure), weight=0.20))

    # Pedagogy: Socratic approach (doesn't give answer directly)
    pedagogy = 70
    answer = getattr(output, "answer_markdown", "") or ""
    # Check for question marks (Socratic questioning)
    if "?" in answer:
        pedagogy += 15
    # Check for step-by-step guidance
    steps = getattr(output, "step_by_step", []) or []
    if len(steps) >= 1:
        pedagogy += 15
    dims.append(RubricDimension("pedagogy", min(100, max(0, pedagogy)), weight=0.30))

    # Safety: educational context preserved
    safety = 100
    content_str = answer.lower()
    # Should not give complete answers to homework
    direct_answer_markers = scenario.get("direct_answer_markers", [])
    for marker in direct_answer_markers:
        if marker.lower() in content_str:
            safety -= 20
    dims.append(RubricDimension("safety", max(0, safety), weight=0.20))

    # Responsiveness: addresses the student's actual question
    responsiveness = 30 if answer else 0
    expected_keywords = scenario.get("expected_keywords", [])
    for kw in expected_keywords:
        if kw.lower() in content_str:
            responsiveness += 12
    dims.append(
        RubricDimension("responsiveness", min(100, max(0, responsiveness)), weight=0.30)
    )

    final = compute_rubric_score(dims)
    threshold = scenario.get("threshold", 70.0)
    return RubricResult(
        agent_type="tutor",
        scenario_id=scenario.get("id", "unknown"),
        dimensions=tuple(dims),
        final_score=final,
        passed=final >= threshold,
        threshold=threshold,
    )


# --- Regression detection ---


@dataclass(frozen=True)
class RegressionReport:
    """Comparison of current vs. baseline rubric scores."""

    scenario_id: str
    agent_type: str
    current_score: float
    baseline_score: float
    delta: float
    regressed: bool  # True if current < baseline - tolerance
    tolerance: float = 5.0

    @property
    def improved(self) -> bool:
        return self.delta > self.tolerance


def detect_regressions(
    current_results: list[RubricResult],
    baseline_results: list[RubricResult],
    tolerance: float = 5.0,
) -> list[RegressionReport]:
    """Compare current eval results against a baseline.

    Returns a report per scenario. A regression is flagged when the
    current score drops below (baseline - tolerance).
    """
    baseline_map = {r.scenario_id: r for r in baseline_results}
    reports: list[RegressionReport] = []

    for current in current_results:
        baseline = baseline_map.get(current.scenario_id)
        if baseline is None:
            continue  # new scenario, no baseline to compare

        delta = current.final_score - baseline.final_score
        reports.append(
            RegressionReport(
                scenario_id=current.scenario_id,
                agent_type=current.agent_type,
                current_score=current.final_score,
                baseline_score=baseline.final_score,
                delta=round(delta, 2),
                regressed=delta < -tolerance,
                tolerance=tolerance,
            )
        )

    return reports
