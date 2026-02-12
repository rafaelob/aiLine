"""Tests for QualityAssessment and ExecutorResult Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ailine_agents.models import ExecutorResult, QualityAssessment


class TestQualityAssessment:
    """QualityAssessment: score 0-100 with status, errors, warnings, etc."""

    def test_valid_creation(self) -> None:
        qa = QualityAssessment(
            score=85,
            status="accept",
            errors=[],
            warnings=["minor issue"],
            recommendations=["improve glossary"],
            checklist={"has_steps": True, "has_instructions": True},
            human_review_required=False,
            human_review_reasons=[],
        )
        assert qa.score == 85
        assert qa.status == "accept"
        assert qa.warnings == ["minor issue"]

    def test_score_min_boundary(self) -> None:
        qa = QualityAssessment(score=0, status="must-refine")
        assert qa.score == 0

    def test_score_max_boundary(self) -> None:
        qa = QualityAssessment(score=100, status="accept")
        assert qa.score == 100

    def test_score_below_min_rejected(self) -> None:
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            QualityAssessment(score=-1, status="must-refine")

    def test_score_above_max_rejected(self) -> None:
        with pytest.raises(ValidationError, match="less than or equal to 100"):
            QualityAssessment(score=101, status="accept")

    def test_defaults(self) -> None:
        qa = QualityAssessment(score=70, status="refine-if-budget")
        assert qa.errors == []
        assert qa.warnings == []
        assert qa.recommendations == []
        assert qa.checklist == {}
        assert qa.human_review_required is False
        assert qa.human_review_reasons == []

    def test_model_dump(self) -> None:
        qa = QualityAssessment(score=75, status="refine-if-budget", errors=["missing steps"])
        d = qa.model_dump()
        assert d["score"] == 75
        assert d["status"] == "refine-if-budget"
        assert d["errors"] == ["missing steps"]
        assert "warnings" in d
        assert "checklist" in d

    def test_missing_score_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QualityAssessment(status="accept")  # type: ignore[call-arg]

    def test_missing_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            QualityAssessment(score=50)  # type: ignore[call-arg]


class TestExecutorResult:
    """ExecutorResult: plan output from the executor agent."""

    def test_valid_creation(self) -> None:
        er = ExecutorResult(
            plan_id="p-1",
            plan_json={"title": "My Plan"},
            accessibility_report={"score": 90},
            exports={"standard_html": "<html>...</html>"},
            score=88,
            human_review_required=True,
            summary_bullets=["Generated 5 steps", "Accessibility: 90"],
        )
        assert er.plan_id == "p-1"
        assert er.plan_json == {"title": "My Plan"}
        assert er.exports == {"standard_html": "<html>...</html>"}
        assert er.score == 88
        assert er.human_review_required is True
        assert len(er.summary_bullets) == 2

    def test_defaults(self) -> None:
        er = ExecutorResult()
        assert er.plan_id == ""
        assert er.plan_json == {}
        assert er.accessibility_report == {}
        assert er.exports == {}
        assert er.score == 0
        assert er.human_review_required is False
        assert er.summary_bullets == []

    def test_model_dump(self) -> None:
        er = ExecutorResult(plan_id="abc", score=42)
        d = er.model_dump()
        assert d["plan_id"] == "abc"
        assert d["score"] == 42
        assert isinstance(d["plan_json"], dict)
        assert isinstance(d["summary_bullets"], list)
