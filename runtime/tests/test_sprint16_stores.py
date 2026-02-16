"""Tests for Sprint 16 in-memory stores.

Covers: ReviewStore (reviews + flags), ProgressStore (record, dashboard, student).
"""

from __future__ import annotations

import threading

from ailine_runtime.domain.entities.plan import ReviewStatus
from ailine_runtime.domain.entities.progress import MasteryLevel
from ailine_runtime.shared.progress_store import ProgressStore
from ailine_runtime.shared.review_store import ReviewStore

# ---------------------------------------------------------------------------
# ReviewStore: plan reviews
# ---------------------------------------------------------------------------


class TestReviewStoreReviews:
    def test_create_review(self) -> None:
        store = ReviewStore()
        review = store.create_review("plan-1", "teacher-1")
        assert review.plan_id == "plan-1"
        assert review.teacher_id == "teacher-1"
        assert review.status == ReviewStatus.PENDING_REVIEW
        assert review.review_id  # non-empty UUID
        assert review.created_at  # non-empty timestamp

    def test_get_review(self) -> None:
        store = ReviewStore()
        store.create_review("plan-1", "teacher-1")
        review = store.get_review("plan-1")
        assert review is not None
        assert review.plan_id == "plan-1"

    def test_get_review_not_found(self) -> None:
        store = ReviewStore()
        assert store.get_review("nonexistent") is None

    def test_update_review_approve(self) -> None:
        store = ReviewStore()
        store.create_review("plan-1", "teacher-1")
        updated = store.update_review("plan-1", ReviewStatus.APPROVED, "Looks good")
        assert updated is not None
        assert updated.status == ReviewStatus.APPROVED
        assert updated.notes == "Looks good"
        assert updated.approved_at is not None  # set for APPROVED

    def test_update_review_reject(self) -> None:
        store = ReviewStore()
        store.create_review("plan-1", "teacher-1")
        updated = store.update_review(
            "plan-1", ReviewStatus.REJECTED, "Needs more work"
        )
        assert updated is not None
        assert updated.status == ReviewStatus.REJECTED
        assert updated.approved_at is not None  # set for REJECTED too

    def test_update_review_needs_revision(self) -> None:
        store = ReviewStore()
        store.create_review("plan-1", "teacher-1")
        updated = store.update_review(
            "plan-1", ReviewStatus.NEEDS_REVISION, "Fix objectives"
        )
        assert updated is not None
        assert updated.status == ReviewStatus.NEEDS_REVISION
        assert updated.approved_at is None  # NOT set for NEEDS_REVISION

    def test_update_review_not_found(self) -> None:
        store = ReviewStore()
        assert store.update_review("nonexistent", ReviewStatus.APPROVED) is None

    def test_list_pending(self) -> None:
        store = ReviewStore()
        store.create_review("plan-1", "teacher-1")
        store.create_review("plan-2", "teacher-1")
        store.create_review("plan-3", "teacher-2")

        # Approve plan-2 so it's no longer pending
        store.update_review("plan-2", ReviewStatus.APPROVED)

        pending = store.list_pending("teacher-1")
        assert len(pending) == 1
        assert pending[0].plan_id == "plan-1"

    def test_list_pending_includes_draft(self) -> None:
        store = ReviewStore()
        store.create_review("plan-1", "teacher-1")
        # Manually set status to DRAFT
        store.update_review("plan-1", ReviewStatus.DRAFT)
        pending = store.list_pending("teacher-1")
        assert len(pending) == 1

    def test_list_all(self) -> None:
        store = ReviewStore()
        store.create_review("plan-1", "teacher-1")
        store.create_review("plan-2", "teacher-1")
        store.create_review("plan-3", "teacher-2")
        store.update_review("plan-2", ReviewStatus.APPROVED)

        all_t1 = store.list_all("teacher-1")
        assert len(all_t1) == 2

        all_t2 = store.list_all("teacher-2")
        assert len(all_t2) == 1

    def test_create_review_replaces_existing(self) -> None:
        store = ReviewStore()
        first = store.create_review("plan-1", "teacher-1")
        second = store.create_review("plan-1", "teacher-1")
        # Second create overwrites
        assert second.review_id != first.review_id
        review = store.get_review("plan-1")
        assert review is not None
        assert review.review_id == second.review_id


# ---------------------------------------------------------------------------
# ReviewStore: tutor turn flags
# ---------------------------------------------------------------------------


class TestReviewStoreFlags:
    def test_add_flag(self) -> None:
        store = ReviewStore()
        flag = store.add_flag("sess-1", 2, "teacher-1", "Incorrect info")
        assert flag.session_id == "sess-1"
        assert flag.turn_index == 2
        assert flag.teacher_id == "teacher-1"
        assert flag.reason == "Incorrect info"
        assert flag.flag_id  # non-empty UUID

    def test_get_flags(self) -> None:
        store = ReviewStore()
        store.add_flag("sess-1", 0, "teacher-1", "R1")
        store.add_flag("sess-1", 3, "teacher-1", "R2")
        store.add_flag("sess-2", 1, "teacher-1", "R3")

        flags_1 = store.get_flags("sess-1")
        assert len(flags_1) == 2
        assert flags_1[0].reason == "R1"
        assert flags_1[1].reason == "R2"

        flags_2 = store.get_flags("sess-2")
        assert len(flags_2) == 1

    def test_get_flags_empty(self) -> None:
        store = ReviewStore()
        assert store.get_flags("nonexistent") == []


# ---------------------------------------------------------------------------
# ProgressStore
# ---------------------------------------------------------------------------


class TestProgressStoreRecord:
    def test_record_new(self) -> None:
        store = ProgressStore()
        p = store.record_progress(
            teacher_id="t1",
            student_id="s1",
            student_name="Alice",
            standard_code="EF06MA01",
            standard_description="Fractions",
            mastery_level=MasteryLevel.DEVELOPING,
        )
        assert p.student_id == "s1"
        assert p.student_name == "Alice"
        assert p.mastery_level == MasteryLevel.DEVELOPING
        assert p.session_count == 1
        assert p.last_activity is not None
        assert p.progress_id  # non-empty UUID

    def test_record_update_existing(self) -> None:
        store = ProgressStore()
        first = store.record_progress(
            teacher_id="t1",
            student_id="s1",
            student_name="Alice",
            standard_code="EF06MA01",
            standard_description="Fractions",
            mastery_level=MasteryLevel.DEVELOPING,
        )
        second = store.record_progress(
            teacher_id="t1",
            student_id="s1",
            student_name="Alice",
            standard_code="EF06MA01",
            standard_description="Fractions",
            mastery_level=MasteryLevel.PROFICIENT,
        )
        # Same record updated, not a new one
        assert first.progress_id == second.progress_id
        assert second.mastery_level == MasteryLevel.PROFICIENT
        assert second.session_count == 2

    def test_record_different_standards_are_separate(self) -> None:
        store = ProgressStore()
        store.record_progress(
            teacher_id="t1",
            student_id="s1",
            student_name="Alice",
            standard_code="EF06MA01",
            standard_description="",
            mastery_level=MasteryLevel.DEVELOPING,
        )
        store.record_progress(
            teacher_id="t1",
            student_id="s1",
            student_name="Alice",
            standard_code="EF06MA02",
            standard_description="",
            mastery_level=MasteryLevel.MASTERED,
        )
        records = store.get_student("t1", "s1")
        assert len(records) == 2

    def test_record_preserves_notes_on_update_if_empty(self) -> None:
        store = ProgressStore()
        store.record_progress(
            teacher_id="t1",
            student_id="s1",
            student_name="Alice",
            standard_code="C1",
            standard_description="",
            mastery_level=MasteryLevel.DEVELOPING,
            notes="Initial note",
        )
        updated = store.record_progress(
            teacher_id="t1",
            student_id="s1",
            student_name="Alice",
            standard_code="C1",
            standard_description="",
            mastery_level=MasteryLevel.PROFICIENT,
            notes="",  # empty => preserve old
        )
        assert updated.notes == "Initial note"

    def test_record_overwrites_notes_on_update(self) -> None:
        store = ProgressStore()
        store.record_progress(
            teacher_id="t1",
            student_id="s1",
            student_name="Alice",
            standard_code="C1",
            standard_description="",
            mastery_level=MasteryLevel.DEVELOPING,
            notes="Old note",
        )
        updated = store.record_progress(
            teacher_id="t1",
            student_id="s1",
            student_name="Alice",
            standard_code="C1",
            standard_description="",
            mastery_level=MasteryLevel.PROFICIENT,
            notes="New note",
        )
        assert updated.notes == "New note"


class TestProgressStoreDashboard:
    def test_empty_dashboard(self) -> None:
        store = ProgressStore()
        dashboard = store.get_dashboard("t1")
        assert dashboard.teacher_id == "t1"
        assert dashboard.total_students == 0
        assert dashboard.total_standards == 0
        assert dashboard.students == []
        assert dashboard.standards == []

    def test_dashboard_aggregation(self) -> None:
        store = ProgressStore()
        store.record_progress(
            "t1", "s1", "Alice", "C1", "Fractions", MasteryLevel.MASTERED
        )
        store.record_progress(
            "t1", "s1", "Alice", "C2", "Decimals", MasteryLevel.PROFICIENT
        )
        store.record_progress(
            "t1", "s2", "Bob", "C1", "Fractions", MasteryLevel.DEVELOPING
        )

        dashboard = store.get_dashboard("t1")
        assert dashboard.total_students == 2
        assert dashboard.total_standards == 2
        assert dashboard.mastery_distribution["mastered"] == 1
        assert dashboard.mastery_distribution["proficient"] == 1
        assert dashboard.mastery_distribution["developing"] == 1

    def test_dashboard_student_summaries(self) -> None:
        store = ProgressStore()
        store.record_progress("t1", "s1", "Alice", "C1", "", MasteryLevel.MASTERED)
        store.record_progress("t1", "s1", "Alice", "C2", "", MasteryLevel.PROFICIENT)

        dashboard = store.get_dashboard("t1")
        assert len(dashboard.students) == 1
        alice = dashboard.students[0]
        assert alice.student_id == "s1"
        assert alice.student_name == "Alice"
        assert alice.standards_count == 2
        assert alice.mastered_count == 1
        assert alice.proficient_count == 1

    def test_dashboard_standard_summaries(self) -> None:
        store = ProgressStore()
        store.record_progress(
            "t1", "s1", "Alice", "C1", "Fractions", MasteryLevel.MASTERED
        )
        store.record_progress(
            "t1", "s2", "Bob", "C1", "Fractions", MasteryLevel.DEVELOPING
        )

        dashboard = store.get_dashboard("t1")
        assert len(dashboard.standards) == 1
        std = dashboard.standards[0]
        assert std.standard_code == "C1"
        assert std.student_count == 2
        assert std.mastered_count == 1
        assert std.developing_count == 1

    def test_dashboard_isolation_between_teachers(self) -> None:
        store = ProgressStore()
        store.record_progress("t1", "s1", "Alice", "C1", "", MasteryLevel.MASTERED)
        store.record_progress("t2", "s2", "Bob", "C1", "", MasteryLevel.DEVELOPING)

        d1 = store.get_dashboard("t1")
        d2 = store.get_dashboard("t2")
        assert d1.total_students == 1
        assert d2.total_students == 1


class TestProgressStoreGetStudent:
    def test_get_student(self) -> None:
        store = ProgressStore()
        store.record_progress("t1", "s1", "Alice", "C1", "", MasteryLevel.MASTERED)
        store.record_progress("t1", "s1", "Alice", "C2", "", MasteryLevel.DEVELOPING)
        store.record_progress("t1", "s2", "Bob", "C1", "", MasteryLevel.PROFICIENT)

        records = store.get_student("t1", "s1")
        assert len(records) == 2
        assert all(r.student_id == "s1" for r in records)

    def test_get_student_empty(self) -> None:
        store = ProgressStore()
        assert store.get_student("t1", "nonexistent") == []

    def test_get_student_teacher_isolation(self) -> None:
        store = ProgressStore()
        store.record_progress("t1", "s1", "Alice", "C1", "", MasteryLevel.MASTERED)
        store.record_progress("t2", "s1", "Alice", "C1", "", MasteryLevel.DEVELOPING)

        t1_records = store.get_student("t1", "s1")
        t2_records = store.get_student("t2", "s1")
        assert len(t1_records) == 1
        assert t1_records[0].mastery_level == MasteryLevel.MASTERED
        assert len(t2_records) == 1
        assert t2_records[0].mastery_level == MasteryLevel.DEVELOPING


# ---------------------------------------------------------------------------
# Thread safety (basic)
# ---------------------------------------------------------------------------


class TestProgressStoreThreadSafety:
    def test_concurrent_writes(self) -> None:
        store = ProgressStore()
        errors: list[Exception] = []

        def writer(student_id: str) -> None:
            try:
                for i in range(20):
                    store.record_progress(
                        teacher_id="t1",
                        student_id=student_id,
                        student_name=f"Student {student_id}",
                        standard_code=f"C{i}",
                        standard_description="",
                        mastery_level=MasteryLevel.DEVELOPING,
                    )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(f"s{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        dashboard = store.get_dashboard("t1")
        assert dashboard.total_students == 5
        # Each student has 20 standards
        assert sum(s.standards_count for s in dashboard.students) == 100


class TestReviewStoreThreadSafety:
    def test_concurrent_flag_writes(self) -> None:
        store = ReviewStore()
        errors: list[Exception] = []

        def flagger(session_id: str) -> None:
            try:
                for i in range(20):
                    store.add_flag(session_id, i, "teacher-1", f"reason-{i}")
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=flagger, args=(f"sess-{i}",)) for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        total_flags = sum(len(store.get_flags(f"sess-{i}")) for i in range(5))
        assert total_flags == 100
