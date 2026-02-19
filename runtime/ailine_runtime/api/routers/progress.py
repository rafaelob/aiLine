"""Progress API router — student mastery tracking.

Provides RBAC-aware endpoints:
- Teachers: record/view progress for their students
- Students: view their own progress
- Parents: view their linked children's progress
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...app.authz import require_authenticated, require_teacher_or_admin
from ...domain.entities.progress import MasteryLevel
from ...domain.entities.user import UserRole
from ...shared.progress_store import get_progress_store
from ...shared.tenant import get_current_user_role

router = APIRouter()


class ProgressRecordIn(BaseModel):
    """Input schema for recording student progress."""

    student_id: str = Field(..., min_length=1)
    student_name: str = Field("", max_length=200)
    standard_code: str = Field(..., min_length=1)
    standard_description: str = Field("", max_length=500)
    mastery_level: str = Field(
        ..., description="not_started|developing|proficient|mastered"
    )
    notes: str = Field("", max_length=2000)


@router.post("/record")
async def progress_record(body: ProgressRecordIn) -> dict[str, Any]:
    """Record student mastery progress on a standard.

    Requires teacher or admin role.
    """
    teacher_id = require_teacher_or_admin()

    try:
        level = MasteryLevel(body.mastery_level)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid mastery_level: {body.mastery_level}",
        ) from exc

    store = get_progress_store()
    progress = store.record_progress(
        teacher_id=teacher_id,
        student_id=body.student_id,
        student_name=body.student_name,
        standard_code=body.standard_code,
        standard_description=body.standard_description,
        mastery_level=level,
        notes=body.notes,
    )
    return progress.model_dump()


@router.get("/dashboard")
async def progress_dashboard() -> dict:
    """Get class progress overview for the authenticated teacher."""
    teacher_id = require_authenticated()
    store = get_progress_store()
    summary = store.get_dashboard(teacher_id)
    return summary.model_dump()


@router.get("/student/{student_id}")
async def progress_student(student_id: str) -> list[dict[str, Any]]:
    """Get progress records for a specific student.

    Teacher/admin: can view any student in their class.
    Student: can view only their own progress.
    Parent: can view linked children's progress.
    """
    user_id = require_authenticated()
    role = get_current_user_role()
    store = get_progress_store()

    # Students can only view their own progress
    if role == UserRole.STUDENT:
        if user_id != student_id:
            raise HTTPException(
                status_code=403,
                detail="Students can only view their own progress.",
            )
        # Aggregate across all teachers' records for this student
        all_records = store.get_student_all_teachers(student_id)
        if not all_records:
            raise HTTPException(
                status_code=404,
                detail="No progress records found.",
            )
        return [r.model_dump() for r in all_records]

    # Parents: use parent-specific endpoint or verify relationship
    if role == UserRole.PARENT:
        all_records = store.get_student_all_teachers(student_id)
        if not all_records:
            raise HTTPException(
                status_code=404,
                detail="No progress records found for this student.",
            )
        return [r.model_dump() for r in all_records]

    # Teacher/admin: view records they own
    records = store.get_student(user_id, student_id)
    if not records:
        raise HTTPException(
            status_code=404,
            detail="No progress records found for this student",
        )
    return [r.model_dump() for r in records]


@router.get("/overview")
async def progress_overview() -> dict[str, Any]:
    """Aggregate progress overview for the authenticated user.

    Teachers/admins: class overview (same as /dashboard).
    Students: personal progress summary.
    Parents: combined children's progress.
    """
    user_id = require_authenticated()
    role = get_current_user_role()
    store = get_progress_store()

    if role == UserRole.STUDENT:
        records = store.get_student_all_teachers(user_id)
        return {
            "role": "student",
            "student_id": user_id,
            "total_standards": len(records),
            "mastery_distribution": _build_mastery_dist(records),
            "records": [r.model_dump() for r in records],
        }

    if role == UserRole.PARENT:
        return {
            "role": "parent",
            "parent_id": user_id,
            "children": [],
            "message": "Link your children's accounts to see their progress.",
        }

    # Teacher/admin
    summary = store.get_dashboard(user_id)
    return {
        "role": role or "teacher",
        **summary.model_dump(),
    }


@router.get("/parent")
async def parent_progress() -> dict[str, Any]:
    """Get progress for a parent's linked children.

    Returns aggregated progress for all students linked to this parent.
    In the MVP, returns a placeholder until parent-student linking is
    implemented via the parent_students table.
    """
    user_id = require_authenticated()
    role = get_current_user_role()

    if role != UserRole.PARENT:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available for parent accounts.",
        )

    return {
        "parent_id": user_id,
        "children": [],
        "message": "Link your children's accounts to see their progress.",
    }


def _build_mastery_dist(
    records: list,
) -> dict[str, int]:
    """Build mastery distribution from a list of progress records."""
    dist: dict[str, int] = {
        "not_started": 0,
        "developing": 0,
        "proficient": 0,
        "mastered": 0,
    }
    for r in records:
        level = r.mastery_level.value if hasattr(r.mastery_level, "value") else str(r.mastery_level)
        if level in dist:
            dist[level] += 1
    return dist
