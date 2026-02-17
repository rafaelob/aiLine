"""In-memory progress store for student mastery tracking.

Simple dict-based storage for hackathon MVP. Production would use DB.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from datetime import UTC, datetime

from uuid_utils import uuid7

from ..domain.entities.progress import (
    ClassProgressSummary,
    LearnerProgress,
    MasteryLevel,
    StandardSummary,
    StudentSummary,
)


class ProgressStore:
    """Thread-safe in-memory store for learner progress."""

    def __init__(self) -> None:
        self._records: dict[str, list[LearnerProgress]] = defaultdict(list)
        self._lock = threading.Lock()

    def record_progress(
        self,
        teacher_id: str,
        student_id: str,
        student_name: str,
        standard_code: str,
        standard_description: str,
        mastery_level: MasteryLevel,
        notes: str = "",
    ) -> LearnerProgress:
        """Record or update a student's mastery on a standard."""
        with self._lock:
            existing = None
            for r in self._records[teacher_id]:
                if r.student_id == student_id and r.standard_code == standard_code:
                    existing = r
                    break

            now = datetime.now(UTC).isoformat()

            if existing:
                existing.mastery_level = mastery_level
                existing.session_count += 1
                existing.last_activity = now
                existing.notes = notes or existing.notes
                existing.student_name = student_name or existing.student_name
                existing.standard_description = (
                    standard_description or existing.standard_description
                )
                return existing

            progress = LearnerProgress(
                progress_id=str(uuid7()),
                student_id=student_id,
                student_name=student_name,
                teacher_id=teacher_id,
                standard_code=standard_code,
                standard_description=standard_description,
                mastery_level=mastery_level,
                session_count=1,
                last_activity=now,
                created_at=now,
                notes=notes,
            )
            self._records[teacher_id].append(progress)
            return progress

    def get_dashboard(self, teacher_id: str) -> ClassProgressSummary:
        """Build aggregated class progress summary."""
        records = self._records.get(teacher_id, [])

        students: dict[str, StudentSummary] = {}
        standards: dict[str, StandardSummary] = {}
        mastery_dist = {
            "not_started": 0,
            "developing": 0,
            "proficient": 0,
            "mastered": 0,
        }

        for r in records:
            mastery_dist[r.mastery_level.value] = (
                mastery_dist.get(r.mastery_level.value, 0) + 1
            )

            # Student summary
            if r.student_id not in students:
                students[r.student_id] = StudentSummary(
                    student_id=r.student_id,
                    student_name=r.student_name,
                )
            s = students[r.student_id]
            s.standards_count += 1
            if r.mastery_level == MasteryLevel.MASTERED:
                s.mastered_count += 1
            elif r.mastery_level == MasteryLevel.PROFICIENT:
                s.proficient_count += 1
            elif r.mastery_level == MasteryLevel.DEVELOPING:
                s.developing_count += 1
            if r.last_activity and (
                s.last_activity is None or r.last_activity > s.last_activity
            ):
                s.last_activity = r.last_activity

            # Standard summary
            if r.standard_code not in standards:
                standards[r.standard_code] = StandardSummary(
                    standard_code=r.standard_code,
                    standard_description=r.standard_description,
                )
            st = standards[r.standard_code]
            st.student_count += 1
            if r.mastery_level == MasteryLevel.MASTERED:
                st.mastered_count += 1
            elif r.mastery_level == MasteryLevel.PROFICIENT:
                st.proficient_count += 1
            elif r.mastery_level == MasteryLevel.DEVELOPING:
                st.developing_count += 1

        return ClassProgressSummary(
            teacher_id=teacher_id,
            total_students=len(students),
            total_standards=len(standards),
            mastery_distribution=mastery_dist,
            students=list(students.values()),
            standards=list(standards.values()),
        )

    def get_student(self, teacher_id: str, student_id: str) -> list[LearnerProgress]:
        """Get all progress records for a specific student under a teacher."""
        return [
            r for r in self._records.get(teacher_id, []) if r.student_id == student_id
        ]


_store: ProgressStore | None = None
_store_lock = threading.Lock()


def get_progress_store() -> ProgressStore:
    """Get or create the singleton progress store."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = ProgressStore()
    return _store
