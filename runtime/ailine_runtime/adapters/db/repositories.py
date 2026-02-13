"""Typed repository implementations for each aggregate root.

Every repository requires an ``AsyncSession`` and scopes queries by
``teacher_id`` where applicable (tenant safety). Methods follow a
consistent CRUD pattern: get, list_by, add, update, delete.

These are thin data-access wrappers; domain logic stays in the domain layer.

BaseRepository[T] provides common CRUD operations with TeacherId scoping
for tenant-safe aggregates (FINDING-03).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .models import (
    CourseRow,
    LessonRow,
    MaterialRow,
    PipelineRunRow,
    TeacherRow,
)

T = TypeVar("T", bound=DeclarativeBase)


# ---------------------------------------------------------------------------
# Base Repository (Generic)
# ---------------------------------------------------------------------------


class BaseRepository(Generic[T]):
    """Generic repository providing common CRUD operations with tenant scoping.

    Subclasses set ``_model`` to the SQLAlchemy model class.
    Methods that require tenant scoping accept ``teacher_id`` and filter
    using the model's ``teacher_id`` column when present.
    """

    _model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> T | None:
        """Fetch an entity by primary key (no tenant scoping)."""
        return await self._session.get(self._model, entity_id)

    async def get_by_id_and_teacher(self, entity_id: str, teacher_id: str) -> T | None:
        """Fetch an entity by PK, scoped to a teacher."""
        # type: ignore[attr-defined] below: SQLAlchemy column attrs on generic T
        stmt = select(self._model).where(
            self._model.id == entity_id,  # type: ignore[attr-defined]
            self._model.teacher_id == teacher_id,  # type: ignore[attr-defined]
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_teacher(self, teacher_id: str) -> Sequence[T]:
        """List all entities for a teacher, ordered by created_at desc."""
        stmt = (
            select(self._model)
            .where(self._model.teacher_id == teacher_id)  # type: ignore[attr-defined]
            .order_by(self._model.created_at.desc())  # type: ignore[attr-defined]
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def add(self, row: T) -> T:
        """Insert a new entity."""
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_fields_by_id_and_teacher(
        self,
        entity_id: str,
        teacher_id: str,
        **fields: object,
    ) -> None:
        """Update specific fields on an entity, scoped to the teacher."""
        stmt = (
            update(self._model)
            .where(
                self._model.id == entity_id,  # type: ignore[attr-defined]
                self._model.teacher_id == teacher_id,  # type: ignore[attr-defined]
            )
            .values(**fields)
        )
        await self._session.execute(stmt)

    async def delete_by_id_and_teacher(self, entity_id: str, teacher_id: str) -> None:
        """Delete an entity, scoped to the teacher."""
        stmt = delete(self._model).where(
            self._model.id == entity_id,  # type: ignore[attr-defined]
            self._model.teacher_id == teacher_id,  # type: ignore[attr-defined]
        )
        await self._session.execute(stmt)


# ---------------------------------------------------------------------------
# Teacher Repository
# ---------------------------------------------------------------------------


class TeacherRepository:
    """Data access for the Teacher aggregate.

    Teacher is the top-level tenant anchor, so it does NOT use
    BaseRepository (no teacher_id scoping on itself).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, teacher_id: str) -> TeacherRow | None:
        """Fetch a teacher by primary key."""
        return await self._session.get(TeacherRow, teacher_id)

    async def get_by_email(self, email: str) -> TeacherRow | None:
        """Fetch a teacher by email address."""
        stmt = select(TeacherRow).where(TeacherRow.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[TeacherRow]:
        """Return all teachers (admin use only)."""
        stmt = select(TeacherRow).order_by(TeacherRow.created_at.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def add(self, row: TeacherRow) -> TeacherRow:
        """Insert a new teacher row."""
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_fields(
        self,
        teacher_id: str,
        **fields: object,
    ) -> None:
        """Update specific fields on a teacher row."""
        stmt = (
            update(TeacherRow)
            .where(TeacherRow.id == teacher_id)
            .values(**fields)
        )
        await self._session.execute(stmt)

    async def delete(self, teacher_id: str) -> None:
        """Delete a teacher by primary key (cascades to children)."""
        stmt = delete(TeacherRow).where(TeacherRow.id == teacher_id)
        await self._session.execute(stmt)


# ---------------------------------------------------------------------------
# Course Repository
# ---------------------------------------------------------------------------


class CourseRepository(BaseRepository[CourseRow]):
    """Data access for the Course aggregate, scoped by teacher_id."""

    _model = CourseRow

    async def get(self, course_id: str, teacher_id: str) -> CourseRow | None:
        """Fetch a course by PK, scoped to the teacher."""
        return await self.get_by_id_and_teacher(course_id, teacher_id)

    async def list_by_teacher(self, teacher_id: str) -> Sequence[CourseRow]:
        """List all courses for a teacher."""
        return await super().list_by_teacher(teacher_id)

    async def add(self, row: CourseRow) -> CourseRow:
        """Insert a new course."""
        return await super().add(row)

    async def update_fields(
        self,
        course_id: str,
        teacher_id: str,
        **fields: object,
    ) -> None:
        """Update specific fields on a course, scoped to the teacher."""
        await self.update_fields_by_id_and_teacher(course_id, teacher_id, **fields)

    async def delete(self, course_id: str, teacher_id: str) -> None:
        """Delete a course, scoped to the teacher."""
        await self.delete_by_id_and_teacher(course_id, teacher_id)


# ---------------------------------------------------------------------------
# Lesson Repository
# ---------------------------------------------------------------------------


class LessonRepository(BaseRepository[LessonRow]):
    """Data access for the Lesson aggregate, scoped by teacher_id."""

    _model = LessonRow

    async def get(self, lesson_id: str, teacher_id: str) -> LessonRow | None:
        """Fetch a lesson by PK, scoped to the teacher."""
        return await self.get_by_id_and_teacher(lesson_id, teacher_id)

    async def list_by_course(
        self,
        course_id: str,
        teacher_id: str,
    ) -> Sequence[LessonRow]:
        """List lessons for a course, scoped to the teacher."""
        stmt = (
            select(LessonRow)
            .where(
                LessonRow.course_id == course_id,
                LessonRow.teacher_id == teacher_id,
            )
            .order_by(LessonRow.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def add(self, row: LessonRow) -> LessonRow:
        """Insert a new lesson."""
        return await super().add(row)

    async def update_fields(
        self,
        lesson_id: str,
        teacher_id: str,
        **fields: object,
    ) -> None:
        """Update specific fields on a lesson, scoped to the teacher."""
        await self.update_fields_by_id_and_teacher(lesson_id, teacher_id, **fields)

    async def delete(self, lesson_id: str, teacher_id: str) -> None:
        """Delete a lesson, scoped to the teacher."""
        await self.delete_by_id_and_teacher(lesson_id, teacher_id)


# ---------------------------------------------------------------------------
# Material Repository
# ---------------------------------------------------------------------------


class MaterialRepository(BaseRepository[MaterialRow]):
    """Data access for the Material aggregate, scoped by teacher_id."""

    _model = MaterialRow

    async def get(self, material_id: str, teacher_id: str) -> MaterialRow | None:
        """Fetch a material by PK, scoped to the teacher."""
        return await self.get_by_id_and_teacher(material_id, teacher_id)

    async def list_by_teacher(
        self,
        teacher_id: str,
        *,
        subject: str | None = None,
    ) -> Sequence[MaterialRow]:
        """List materials for a teacher, optionally filtered by subject."""
        stmt = select(MaterialRow).where(MaterialRow.teacher_id == teacher_id)
        if subject is not None:
            stmt = stmt.where(MaterialRow.subject == subject)
        stmt = stmt.order_by(MaterialRow.created_at.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def add(self, row: MaterialRow) -> MaterialRow:
        """Insert a new material."""
        return await super().add(row)

    async def delete(self, material_id: str, teacher_id: str) -> None:
        """Delete a material, scoped to the teacher."""
        await self.delete_by_id_and_teacher(material_id, teacher_id)


# ---------------------------------------------------------------------------
# PipelineRun Repository
# ---------------------------------------------------------------------------


class PipelineRunRepository(BaseRepository[PipelineRunRow]):
    """Data access for the PipelineRun aggregate, scoped by teacher_id."""

    _model = PipelineRunRow

    async def get(self, run_id: str, teacher_id: str) -> PipelineRunRow | None:
        """Fetch a pipeline run by PK, scoped to the teacher."""
        return await self.get_by_id_and_teacher(run_id, teacher_id)

    async def list_by_teacher(
        self,
        teacher_id: str,
        *,
        status: str | None = None,
    ) -> Sequence[PipelineRunRow]:
        """List pipeline runs for a teacher, optionally filtered by status."""
        stmt = select(PipelineRunRow).where(
            PipelineRunRow.teacher_id == teacher_id,
        )
        if status is not None:
            stmt = stmt.where(PipelineRunRow.status == status)
        stmt = stmt.order_by(PipelineRunRow.created_at.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def add(self, row: PipelineRunRow) -> PipelineRunRow:
        """Insert a new pipeline run."""
        return await super().add(row)

    async def update_fields(
        self,
        run_id: str,
        teacher_id: str,
        **fields: object,
    ) -> None:
        """Update specific fields on a pipeline run, scoped to the teacher."""
        await self.update_fields_by_id_and_teacher(run_id, teacher_id, **fields)
