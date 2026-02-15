"""SQLAlchemy ORM models for the AiLine database layer.

All tables use UUID v7 string primary keys (via uuid-utils) and
timezone-aware timestamps. JSON columns store plain dicts; domain
model validation happens explicitly via Pydantic model_validate()
in the mapper/repository layer.

Composite FK on lessons enforces tenant safety at the DB level (ADR-053).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON
from uuid_utils import uuid7


class Base(DeclarativeBase):
    """Declarative base for all AiLine ORM models."""

    # Use generic JSON type so aiosqlite works in tests.
    # Postgres will use JSONB via the dialect automatically.
    type_annotation_map: ClassVar[dict] = {
        dict: JSON,
        list: JSON,
    }


def _uuid7_str() -> str:
    """Generate a UUID v7 string for use as a primary key default."""
    return str(uuid7())


def _utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Teachers
# ---------------------------------------------------------------------------


class TeacherRow(Base):
    """Teacher entity -- top-level tenant anchor."""

    __tablename__ = "teachers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="pt-BR")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=_utcnow)

    # Relationships
    courses: Mapped[list[CourseRow]] = relationship(back_populates="teacher", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------


class CourseRow(Base):
    """Course owned by a teacher."""

    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    teacher_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[str] = mapped_column(String(50), nullable=False)
    standard: Mapped[str] = mapped_column(String(20), default="BNCC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    teacher: Mapped[TeacherRow] = relationship(back_populates="courses")
    lessons: Mapped[list[LessonRow]] = relationship(back_populates="course", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Lessons -- composite FK to courses for tenant safety (ADR-053)
# ---------------------------------------------------------------------------


class LessonRow(Base):
    """Lesson within a course. Composite FK prevents cross-tenant association."""

    __tablename__ = "lessons"
    __table_args__ = (
        ForeignKeyConstraint(
            ["teacher_id", "course_id"],
            ["courses.teacher_id", "courses.id"],
            ondelete="CASCADE",
        ),
        Index("ix_lessons_teacher_course", "teacher_id", "course_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    teacher_id: Mapped[str] = mapped_column(String(36), nullable=False)
    course_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    plan_json: Mapped[dict] = mapped_column(JSON, default=dict)
    student_plan_json: Mapped[dict] = mapped_column(JSON, default=dict)
    accessibility_json: Mapped[dict] = mapped_column(JSON, default=dict)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=_utcnow)

    # Relationships
    course: Mapped[CourseRow] = relationship(back_populates="lessons")


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------


class MaterialRow(Base):
    """Teacher-uploaded educational material."""

    __tablename__ = "materials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    teacher_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Chunks (embedding vector added via pgvector in migration, not in ORM)
# ---------------------------------------------------------------------------


class ChunkRow(Base):
    """A chunk of material text, ready for embedding and vector search.

    Composite FK (teacher_id, material_id) -> materials(teacher_id, id)
    ensures chunks cannot be associated with materials from a different tenant (ADR-053).
    """

    __tablename__ = "chunks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["teacher_id", "material_id"],
            ["materials.teacher_id", "materials.id"],
            ondelete="CASCADE",
        ),
        Index("ix_chunks_teacher_material", "teacher_id", "material_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    teacher_id: Mapped[str] = mapped_column(String(36), nullable=False)
    material_id: Mapped[str] = mapped_column(String(36), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    # Note: embedding vector column is added by pgvector migration only,
    # not declared here, to keep the ORM portable to aiosqlite for tests.


# ---------------------------------------------------------------------------
# Pipeline Runs
# ---------------------------------------------------------------------------


class PipelineRunRow(Base):
    """Tracks the lifecycle of a plan generation pipeline run.

    Composite FK (teacher_id, lesson_id) -> lessons(teacher_id, id)
    ensures pipeline runs cannot reference lessons from a different tenant (ADR-053).
    """

    __tablename__ = "pipeline_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["teacher_id", "lesson_id"],
            ["lessons.teacher_id", "lessons.id"],
            ondelete="SET NULL",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    teacher_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )
    input_json: Mapped[dict] = mapped_column(JSON, default=dict)
    output_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Tutor Agents
# ---------------------------------------------------------------------------


class TutorAgentRow(Base):
    """Configured tutor agent specification owned by a teacher."""

    __tablename__ = "tutor_agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    teacher_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[str] = mapped_column(String(50), nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, default=dict)
    persona_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Tutor Sessions
# ---------------------------------------------------------------------------


class TutorSessionRow(Base):
    """Conversational state for a tutoring session.

    Composite FK (teacher_id, tutor_id) -> tutor_agents(teacher_id, id)
    ensures sessions cannot reference tutor agents from a different tenant (ADR-053).
    """

    __tablename__ = "tutor_sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["teacher_id", "tutor_id"],
            ["tutor_agents.teacher_id", "tutor_agents.id"],
            ondelete="CASCADE",
        ),
        Index("ix_tutor_sessions_teacher_tutor", "teacher_id", "tutor_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    teacher_id: Mapped[str] = mapped_column(String(36), nullable=False)
    tutor_id: Mapped[str] = mapped_column(String(36), nullable=False)
    messages_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=_utcnow)


# ---------------------------------------------------------------------------
# Curriculum Objectives
# ---------------------------------------------------------------------------


class CurriculumObjectiveRow(Base):
    """A single curriculum objective from a recognized standard."""

    __tablename__ = "curriculum_objectives"
    __table_args__ = (Index("ix_curriculum_system_grade", "system", "grade"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    system: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[str] = mapped_column(String(50), nullable=False)
    domain: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list] = mapped_column(JSON, default=list)


# ---------------------------------------------------------------------------
# Run Events (SSE event log)
# ---------------------------------------------------------------------------


class RunEventRow(Base):
    """A single SSE event emitted during a pipeline run."""

    __tablename__ = "run_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage: Mapped[str] = mapped_column(String(30), nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    data_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Accessibility Profiles
# ---------------------------------------------------------------------------


class AccessibilityProfileRow(Base):
    """Teacher-defined accessibility profile for a group of students."""

    __tablename__ = "accessibility_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    teacher_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    needs_json: Mapped[dict] = mapped_column(JSON, default=dict)
    supports_json: Mapped[dict] = mapped_column(JSON, default=dict)
    ui_prefs_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
