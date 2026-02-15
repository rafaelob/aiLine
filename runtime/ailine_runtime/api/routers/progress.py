"""Progress API router — student mastery tracking."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...app.authz import require_authenticated
from ...domain.entities.progress import MasteryLevel
from ...shared.progress_store import get_progress_store

router = APIRouter()


class ProgressRecordIn(BaseModel):
    """Input schema for recording student progress."""

    student_id: str = Field(..., min_length=1)
    student_name: str = Field("", max_length=200)
    standard_code: str = Field(..., min_length=1)
    standard_description: str = Field("", max_length=500)
    mastery_level: str = Field(..., description="not_started|developing|proficient|mastered")
    notes: str = Field("", max_length=2000)


@router.post("/record")
async def progress_record(body: ProgressRecordIn) -> dict:
    """Record student mastery progress on a standard."""
    teacher_id = require_authenticated()

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
async def progress_student(student_id: str) -> list[dict]:
    """Get progress records for a specific student."""
    teacher_id = require_authenticated()
    store = get_progress_store()
    records = store.get_student(teacher_id, student_id)
    if not records:
        raise HTTPException(
            status_code=404,
            detail="No progress records found for this student",
        )
    return [r.model_dump() for r in records]
