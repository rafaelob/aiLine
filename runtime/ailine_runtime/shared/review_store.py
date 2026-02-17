"""In-memory review store for plan reviews and tutor turn flags.

Simple dict-based storage for hackathon MVP. Production would use DB.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime

from uuid_utils import uuid7

from ..domain.entities.plan import PlanReview, ReviewStatus
from ..domain.entities.tutor import TutorTurnFlag


class ReviewStore:
    """Thread-safe in-memory store for reviews and flags."""

    def __init__(self) -> None:
        self._reviews: dict[str, PlanReview] = {}  # plan_id -> review
        self._flags: dict[str, list[TutorTurnFlag]] = {}  # session_id -> flags
        self._lock = threading.Lock()

    def create_review(self, plan_id: str, teacher_id: str) -> PlanReview:
        with self._lock:
            review = PlanReview(
                review_id=str(uuid7()),
                plan_id=plan_id,
                teacher_id=teacher_id,
                status=ReviewStatus.PENDING_REVIEW,
                created_at=datetime.now(UTC).isoformat(),
            )
            self._reviews[plan_id] = review
            return review

    def get_review(self, plan_id: str) -> PlanReview | None:
        return self._reviews.get(plan_id)

    def update_review(
        self, plan_id: str, status: ReviewStatus, notes: str = ""
    ) -> PlanReview | None:
        with self._lock:
            review = self._reviews.get(plan_id)
            if review is None:
                return None
            review.status = status
            review.notes = notes
            if status in (ReviewStatus.APPROVED, ReviewStatus.REJECTED):
                review.approved_at = datetime.now(UTC).isoformat()
            self._reviews[plan_id] = review
            return review

    def list_pending(self, teacher_id: str) -> list[PlanReview]:
        return [
            r
            for r in self._reviews.values()
            if r.teacher_id == teacher_id
            and r.status in (ReviewStatus.PENDING_REVIEW, ReviewStatus.DRAFT)
        ]

    def list_all(self, teacher_id: str) -> list[PlanReview]:
        return [r for r in self._reviews.values() if r.teacher_id == teacher_id]

    def add_flag(
        self, session_id: str, turn_index: int, teacher_id: str, reason: str
    ) -> TutorTurnFlag:
        with self._lock:
            flag = TutorTurnFlag(
                flag_id=str(uuid7()),
                session_id=session_id,
                turn_index=turn_index,
                teacher_id=teacher_id,
                reason=reason,
                created_at=datetime.now(UTC).isoformat(),
            )
            self._flags.setdefault(session_id, []).append(flag)
            return flag

    def get_flags(self, session_id: str) -> list[TutorTurnFlag]:
        return self._flags.get(session_id, [])


_store: ReviewStore | None = None
_store_lock = threading.Lock()


def get_review_store() -> ReviewStore:
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = ReviewStore()
    return _store
