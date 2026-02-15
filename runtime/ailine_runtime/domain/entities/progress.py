"""Student progress tracking domain entities.

Pure Pydantic models for tracking learner mastery across standards.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class MasteryLevel(StrEnum):
    """Mastery progression levels."""

    NOT_STARTED = "not_started"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    MASTERED = "mastered"


class LearnerProgress(BaseModel):
    """Progress record for a student on a specific standard."""

    progress_id: str
    student_id: str = Field(..., description="Student identifier (anonymous).")
    student_name: str = Field("", description="Student display name.")
    teacher_id: str = Field(..., description="Owning teacher.")
    standard_code: str = Field(..., description="Curriculum standard code.")
    standard_description: str = Field("", description="Short description.")
    mastery_level: MasteryLevel = Field(MasteryLevel.NOT_STARTED)
    session_count: int = Field(0, ge=0, description="Number of tutor sessions on this standard.")
    last_activity: str | None = Field(None, description="ISO timestamp of last activity.")
    created_at: str = Field(..., description="ISO timestamp of creation.")
    notes: str = Field("", description="Teacher notes on progress.")


class StudentSummary(BaseModel):
    """Summary of a single student's progress across standards."""

    student_id: str
    student_name: str = ""
    standards_count: int = 0
    mastered_count: int = 0
    proficient_count: int = 0
    developing_count: int = 0
    last_activity: str | None = None


class StandardSummary(BaseModel):
    """Summary of a single standard across students."""

    standard_code: str
    standard_description: str = ""
    student_count: int = 0
    mastered_count: int = 0
    proficient_count: int = 0
    developing_count: int = 0


class ClassProgressSummary(BaseModel):
    """Aggregated progress for a teacher's class."""

    teacher_id: str
    total_students: int = 0
    total_standards: int = 0
    mastery_distribution: dict[str, int] = Field(
        default_factory=lambda: {
            "not_started": 0,
            "developing": 0,
            "proficient": 0,
            "mastered": 0,
        }
    )
    students: list[StudentSummary] = Field(default_factory=list)
    standards: list[StandardSummary] = Field(default_factory=list)
