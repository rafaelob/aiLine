"""Tests for Sprint 16 domain entity models.

Covers: TransformationScorecard, StandardRef, PlanReview, ReviewStatus,
TutorTurnFlag, LearnerProgress, MasteryLevel, ClassProgressSummary,
StudentSummary, StandardSummary.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ailine_runtime.domain.entities.plan import (
    PlanReview,
    ReviewStatus,
    StandardRef,
    TransformationScorecard,
)
from ailine_runtime.domain.entities.progress import (
    ClassProgressSummary,
    LearnerProgress,
    MasteryLevel,
    StandardSummary,
    StudentSummary,
)
from ailine_runtime.domain.entities.tutor import TutorTurnFlag

# ---------------------------------------------------------------------------
# StandardRef
# ---------------------------------------------------------------------------


class TestStandardRef:
    def test_basic_creation(self) -> None:
        ref = StandardRef(code="EF06MA01", description="Understand fractions")
        assert ref.code == "EF06MA01"
        assert ref.description == "Understand fractions"

    def test_default_description(self) -> None:
        ref = StandardRef(code="CCSS.MATH.6.RP.A.1")
        assert ref.description == ""

    def test_requires_code(self) -> None:
        with pytest.raises(ValidationError):
            StandardRef()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# TransformationScorecard
# ---------------------------------------------------------------------------


class TestTransformationScorecard:
    def test_defaults(self) -> None:
        sc = TransformationScorecard()
        assert sc.reading_level_before == 0.0
        assert sc.reading_level_after == 0.0
        assert sc.standards_aligned == []
        assert sc.accessibility_adaptations == []
        assert sc.rag_groundedness == 0.0
        assert sc.quality_score == 0
        assert sc.quality_decision == "pending"
        assert sc.model_used == ""
        assert sc.router_rationale == ""
        assert sc.time_saved_estimate == ""
        assert sc.total_pipeline_time_ms == 0.0
        assert sc.export_variants_count == 0

    def test_full_creation(self) -> None:
        sc = TransformationScorecard(
            reading_level_before=8.5,
            reading_level_after=5.2,
            standards_aligned=[
                StandardRef(code="EF06MA01", description="Fractions"),
                StandardRef(code="EF06MA02", description="Decimals"),
            ],
            accessibility_adaptations=[
                "autism: visual schedule",
                "adhd: short instructions",
            ],
            rag_groundedness=0.85,
            quality_score=92,
            quality_decision="accept",
            model_used="claude-haiku-4-5-20251001",
            router_rationale="Low token count, structured output needed",
            time_saved_estimate="~30 min -> 12s",
            total_pipeline_time_ms=12345.6,
            export_variants_count=10,
        )
        assert sc.reading_level_before == 8.5
        assert len(sc.standards_aligned) == 2
        assert sc.standards_aligned[0].code == "EF06MA01"
        assert len(sc.accessibility_adaptations) == 2
        assert sc.rag_groundedness == 0.85
        assert sc.quality_score == 92
        assert sc.quality_decision == "accept"
        assert sc.export_variants_count == 10

    def test_quality_score_bounds(self) -> None:
        sc = TransformationScorecard(quality_score=0)
        assert sc.quality_score == 0
        sc = TransformationScorecard(quality_score=100)
        assert sc.quality_score == 100

    def test_quality_score_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TransformationScorecard(quality_score=-1)

    def test_quality_score_above_100_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TransformationScorecard(quality_score=101)

    def test_rag_groundedness_bounds(self) -> None:
        sc = TransformationScorecard(rag_groundedness=0.0)
        assert sc.rag_groundedness == 0.0
        sc = TransformationScorecard(rag_groundedness=1.0)
        assert sc.rag_groundedness == 1.0

    def test_rag_groundedness_below_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TransformationScorecard(rag_groundedness=-0.1)

    def test_rag_groundedness_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TransformationScorecard(rag_groundedness=1.1)

    def test_model_dump_round_trip(self) -> None:
        sc = TransformationScorecard(
            quality_score=75,
            quality_decision="refine-if-budget",
            model_used="claude-haiku-4-5-20251001",
        )
        data = sc.model_dump()
        restored = TransformationScorecard(**data)
        assert restored.quality_score == 75
        assert restored.quality_decision == "refine-if-budget"


# ---------------------------------------------------------------------------
# ReviewStatus + PlanReview
# ---------------------------------------------------------------------------


class TestReviewStatus:
    def test_all_values(self) -> None:
        assert ReviewStatus.DRAFT == "draft"
        assert ReviewStatus.PENDING_REVIEW == "pending_review"
        assert ReviewStatus.APPROVED == "approved"
        assert ReviewStatus.REJECTED == "rejected"
        assert ReviewStatus.NEEDS_REVISION == "needs_revision"

    def test_member_count(self) -> None:
        assert len(ReviewStatus) == 5


class TestPlanReview:
    def test_creation(self) -> None:
        review = PlanReview(
            review_id="rev-1",
            plan_id="plan-1",
            teacher_id="teacher-1",
            created_at="2026-02-14T10:00:00Z",
        )
        assert review.status == ReviewStatus.DRAFT
        assert review.notes == ""
        assert review.approved_at is None

    def test_with_all_fields(self) -> None:
        review = PlanReview(
            review_id="rev-2",
            plan_id="plan-2",
            teacher_id="teacher-2",
            status=ReviewStatus.APPROVED,
            notes="Excellent plan.",
            approved_at="2026-02-14T12:00:00Z",
            created_at="2026-02-14T10:00:00Z",
        )
        assert review.status == ReviewStatus.APPROVED
        assert review.notes == "Excellent plan."
        assert review.approved_at == "2026-02-14T12:00:00Z"

    def test_all_statuses(self) -> None:
        for status in ReviewStatus:
            review = PlanReview(
                review_id="r",
                plan_id="p",
                teacher_id="t",
                status=status,
                created_at="2026-01-01T00:00:00Z",
            )
            assert review.status == status

    def test_requires_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            PlanReview()  # type: ignore[call-arg]

    def test_model_dump(self) -> None:
        review = PlanReview(
            review_id="rev-3",
            plan_id="plan-3",
            teacher_id="teacher-3",
            status=ReviewStatus.NEEDS_REVISION,
            notes="Fix objectives",
            created_at="2026-02-14T10:00:00Z",
        )
        data = review.model_dump()
        assert data["status"] == "needs_revision"
        assert data["notes"] == "Fix objectives"


# ---------------------------------------------------------------------------
# TutorTurnFlag
# ---------------------------------------------------------------------------


class TestTutorTurnFlag:
    def test_basic_creation(self) -> None:
        flag = TutorTurnFlag(
            flag_id="flag-1",
            session_id="sess-1",
            turn_index=3,
            teacher_id="teacher-1",
            reason="Incorrect information",
            created_at="2026-02-14T10:00:00Z",
        )
        assert flag.flag_id == "flag-1"
        assert flag.session_id == "sess-1"
        assert flag.turn_index == 3
        assert flag.reason == "Incorrect information"

    def test_turn_index_zero(self) -> None:
        flag = TutorTurnFlag(
            flag_id="f",
            session_id="s",
            turn_index=0,
            teacher_id="t",
            reason="",
            created_at="2026-01-01T00:00:00Z",
        )
        assert flag.turn_index == 0

    def test_turn_index_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TutorTurnFlag(
                flag_id="f",
                session_id="s",
                turn_index=-1,
                teacher_id="t",
                reason="",
                created_at="2026-01-01T00:00:00Z",
            )

    def test_default_reason_empty(self) -> None:
        flag = TutorTurnFlag(
            flag_id="f",
            session_id="s",
            turn_index=0,
            teacher_id="t",
            reason="",
            created_at="2026-01-01T00:00:00Z",
        )
        assert flag.reason == ""

    def test_requires_session_id(self) -> None:
        with pytest.raises(ValidationError):
            TutorTurnFlag(
                flag_id="f",
                turn_index=0,
                teacher_id="t",
                created_at="2026-01-01T00:00:00Z",
            )  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# MasteryLevel + LearnerProgress
# ---------------------------------------------------------------------------


class TestMasteryLevel:
    def test_all_values(self) -> None:
        assert MasteryLevel.NOT_STARTED == "not_started"
        assert MasteryLevel.DEVELOPING == "developing"
        assert MasteryLevel.PROFICIENT == "proficient"
        assert MasteryLevel.MASTERED == "mastered"

    def test_member_count(self) -> None:
        assert len(MasteryLevel) == 4


class TestLearnerProgress:
    def test_creation(self) -> None:
        p = LearnerProgress(
            progress_id="p1",
            student_id="s1",
            student_name="",
            teacher_id="t1",
            standard_code="EF06MA01",
            standard_description="",
            mastery_level=MasteryLevel.NOT_STARTED,
            session_count=0,
            last_activity=None,
            created_at="2026-02-14T10:00:00Z",
            notes="",
        )
        assert p.mastery_level == MasteryLevel.NOT_STARTED
        assert p.session_count == 0
        assert p.last_activity is None
        assert p.notes == ""
        assert p.student_name == ""
        assert p.standard_description == ""

    def test_full_creation(self) -> None:
        p = LearnerProgress(
            progress_id="p2",
            student_id="s2",
            student_name="Alice",
            teacher_id="t1",
            standard_code="EF06MA01",
            standard_description="Understand fractions",
            mastery_level=MasteryLevel.MASTERED,
            session_count=5,
            last_activity="2026-02-14T10:00:00Z",
            created_at="2026-02-10T10:00:00Z",
            notes="Excellent progress",
        )
        assert p.student_name == "Alice"
        assert p.mastery_level == MasteryLevel.MASTERED
        assert p.session_count == 5

    def test_all_mastery_levels(self) -> None:
        for level in MasteryLevel:
            p = LearnerProgress(
                progress_id="p",
                student_id="s",
                student_name="Test",
                teacher_id="t",
                standard_code="C",
                standard_description="Test",
                mastery_level=level,
                session_count=0,
                last_activity=None,
                created_at="2026-01-01T00:00:00Z",
                notes="",
            )
            assert p.mastery_level == level

    def test_session_count_ge_zero(self) -> None:
        with pytest.raises(ValidationError):
            LearnerProgress(
                progress_id="p",
                student_id="s",
                student_name="Test",
                teacher_id="t",
                standard_code="C",
                standard_description="Test",
                mastery_level=MasteryLevel.NOT_STARTED,
                session_count=-1,
                last_activity=None,
                created_at="2026-01-01T00:00:00Z",
                notes="",
            )


# ---------------------------------------------------------------------------
# StudentSummary
# ---------------------------------------------------------------------------


class TestStudentSummary:
    def test_defaults(self) -> None:
        s = StudentSummary(student_id="s1")
        assert s.student_name == ""
        assert s.standards_count == 0
        assert s.mastered_count == 0
        assert s.proficient_count == 0
        assert s.developing_count == 0
        assert s.last_activity is None

    def test_full_creation(self) -> None:
        s = StudentSummary(
            student_id="s1",
            student_name="Alice",
            standards_count=5,
            mastered_count=2,
            proficient_count=2,
            developing_count=1,
            last_activity="2026-02-14T10:00:00Z",
        )
        assert s.mastered_count + s.proficient_count + s.developing_count == 5


# ---------------------------------------------------------------------------
# StandardSummary
# ---------------------------------------------------------------------------


class TestStandardSummary:
    def test_defaults(self) -> None:
        s = StandardSummary(standard_code="EF06MA01")
        assert s.standard_description == ""
        assert s.student_count == 0
        assert s.mastered_count == 0

    def test_full_creation(self) -> None:
        s = StandardSummary(
            standard_code="EF06MA01",
            standard_description="Fractions",
            student_count=10,
            mastered_count=3,
            proficient_count=4,
            developing_count=3,
        )
        assert s.student_count == 10


# ---------------------------------------------------------------------------
# ClassProgressSummary
# ---------------------------------------------------------------------------


class TestClassProgressSummary:
    def test_defaults(self) -> None:
        summary = ClassProgressSummary(teacher_id="t1")
        assert summary.total_students == 0
        assert summary.total_standards == 0
        assert summary.mastery_distribution == {
            "not_started": 0,
            "developing": 0,
            "proficient": 0,
            "mastered": 0,
        }
        assert summary.students == []
        assert summary.standards == []

    def test_with_data(self) -> None:
        summary = ClassProgressSummary(
            teacher_id="t1",
            total_students=3,
            total_standards=2,
            mastery_distribution={
                "not_started": 0,
                "developing": 2,
                "proficient": 3,
                "mastered": 1,
            },
            students=[
                StudentSummary(
                    student_id="s1", student_name="Alice", standards_count=2
                ),
                StudentSummary(student_id="s2", student_name="Bob", standards_count=2),
            ],
            standards=[
                StandardSummary(standard_code="EF06MA01", student_count=3),
            ],
        )
        assert summary.total_students == 3
        assert len(summary.students) == 2
        assert len(summary.standards) == 1

    def test_model_dump(self) -> None:
        summary = ClassProgressSummary(teacher_id="t1", total_students=1)
        data = summary.model_dump()
        assert data["teacher_id"] == "t1"
        assert data["total_students"] == 1
        assert isinstance(data["mastery_distribution"], dict)
