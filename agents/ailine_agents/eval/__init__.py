"""Agent evaluation framework: golden test sets, rubric scoring, regression detection.

Provides:
- EvalRubric: Simple dataclass for multi-dimension scoring (accuracy, safety, pedagogy, structure)
- score_plan_output: Heuristic scoring for planner text output
- score_tutor_response: Heuristic scoring for tutor text responses
- RubricResult / RubricDimension: Detailed rubric scoring from rubric.py
- detect_regressions: Baseline comparison with tolerance
- Golden test sets: PLANNER_GOLDEN, QUALITY_GATE_GOLDEN, TUTOR_GOLDEN
"""

from __future__ import annotations

from .golden_sets import PLANNER_GOLDEN, QUALITY_GATE_GOLDEN, TUTOR_GOLDEN
from .rubric import (
    RegressionReport,
    RubricDimension,
    RubricResult,
    compute_rubric_score,
    detect_regressions,
    score_planner_output,
    score_quality_gate_output,
    score_tutor_output,
)
from .scoring import EvalRubric, score_plan_output, score_tutor_response

__all__ = [
    "PLANNER_GOLDEN",
    "QUALITY_GATE_GOLDEN",
    "TUTOR_GOLDEN",
    "EvalRubric",
    "RegressionReport",
    "RubricDimension",
    "RubricResult",
    "compute_rubric_score",
    "detect_regressions",
    "score_plan_output",
    "score_planner_output",
    "score_quality_gate_output",
    "score_tutor_output",
    "score_tutor_response",
]
