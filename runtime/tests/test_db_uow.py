"""Tests for the SqlAlchemyUnitOfWork implementation.

Covers commit, rollback, context manager lifecycle, and lazy
repository accessor behaviour. Runs against in-memory aiosqlite.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ailine_runtime.adapters.db.models import (
    CourseRow,
    LessonRow,
    MaterialRow,
    PipelineRunRow,
    TeacherRow,
    _uuid7_str,
)
from ailine_runtime.adapters.db.repositories import (
    CourseRepository,
    LessonRepository,
    MaterialRepository,
    PipelineRunRepository,
    TeacherRepository,
)
from ailine_runtime.adapters.db.unit_of_work import SqlAlchemyUnitOfWork

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_teacher(**overrides: str) -> TeacherRow:
    defaults: dict[str, str] = {
        "id": _uuid7_str(),
        "email": "uow-test@ailine.dev",
        "display_name": "UoW Tester",
    }
    defaults.update(overrides)
    return TeacherRow(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# UoW context manager lifecycle
# ---------------------------------------------------------------------------


class TestUnitOfWorkLifecycle:
    async def test_session_available_inside_context(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        uow = SqlAlchemyUnitOfWork(session_factory)
        async with uow:
            assert uow.session is not None

    async def test_session_none_after_exit(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        uow = SqlAlchemyUnitOfWork(session_factory)
        async with uow:
            pass
        with pytest.raises(AssertionError, match="UoW not entered"):
            _ = uow.session

    async def test_commit_outside_context_raises(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        uow = SqlAlchemyUnitOfWork(session_factory)
        with pytest.raises(AssertionError, match="UoW not entered"):
            await uow.commit()

    async def test_rollback_outside_context_raises(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        uow = SqlAlchemyUnitOfWork(session_factory)
        with pytest.raises(AssertionError, match="UoW not entered"):
            await uow.rollback()


# ---------------------------------------------------------------------------
# Commit and rollback
# ---------------------------------------------------------------------------


class TestUnitOfWorkCommitRollback:
    async def test_commit_persists_data(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        teacher = _make_teacher()
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            await uow.teachers.add(teacher)
            await uow.commit()

        # Verify in a separate session
        async with session_factory() as verify_session:
            stmt = select(TeacherRow).where(TeacherRow.id == teacher.id)
            result = await verify_session.execute(stmt)
            row = result.scalar_one_or_none()
            assert row is not None
            assert row.display_name == "UoW Tester"

    async def test_rollback_discards_data(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        teacher = _make_teacher(email="rollback@ailine.dev")
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            await uow.teachers.add(teacher)
            await uow.rollback()

        # Verify data was NOT persisted
        async with session_factory() as verify_session:
            stmt = select(TeacherRow).where(TeacherRow.id == teacher.id)
            result = await verify_session.execute(stmt)
            assert result.scalar_one_or_none() is None

    async def test_exception_triggers_rollback(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        teacher = _make_teacher(email="exception@ailine.dev")
        with pytest.raises(ValueError, match="boom"):
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                await uow.teachers.add(teacher)
                await uow.session.flush()
                raise ValueError("boom")

        # Data should NOT be persisted
        async with session_factory() as verify_session:
            stmt = select(TeacherRow).where(TeacherRow.id == teacher.id)
            result = await verify_session.execute(stmt)
            assert result.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# Lazy repository accessors
# ---------------------------------------------------------------------------


class TestUnitOfWorkRepositories:
    async def test_teachers_repo_type(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            assert isinstance(uow.teachers, TeacherRepository)

    async def test_courses_repo_type(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            assert isinstance(uow.courses, CourseRepository)

    async def test_lessons_repo_type(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            assert isinstance(uow.lessons, LessonRepository)

    async def test_materials_repo_type(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            assert isinstance(uow.materials, MaterialRepository)

    async def test_pipeline_runs_repo_type(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            assert isinstance(uow.pipeline_runs, PipelineRunRepository)

    async def test_repo_cached_on_same_uow(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            r1 = uow.teachers
            r2 = uow.teachers
            assert r1 is r2

    async def test_repos_reset_after_exit(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        uow = SqlAlchemyUnitOfWork(session_factory)
        async with uow:
            _ = uow.teachers  # Access to populate cache
        # After exit, internal caches should be None
        assert uow._teachers is None
        assert uow._courses is None


# ---------------------------------------------------------------------------
# Multi-aggregate workflow through UoW
# ---------------------------------------------------------------------------


class TestUnitOfWorkMultiAggregate:
    async def test_create_teacher_course_lesson(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Full workflow: teacher -> course -> lesson in one UoW."""
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            teacher = _make_teacher(email="workflow@ailine.dev")
            await uow.teachers.add(teacher)

            course = CourseRow(
                teacher_id=teacher.id,
                title="Ciencias",
                subject="Ciencias",
                grade="7o ano",
            )
            await uow.courses.add(course)

            lesson = LessonRow(
                teacher_id=teacher.id,
                course_id=course.id,
                title="Celulas",
            )
            await uow.lessons.add(lesson)
            await uow.commit()

        # Verify
        async with session_factory() as verify_session:
            stmt = select(LessonRow).where(LessonRow.teacher_id == teacher.id)
            result = await verify_session.execute(stmt)
            lessons = result.scalars().all()
            assert len(lessons) == 1
            assert lessons[0].title == "Celulas"
            assert lessons[0].course_id == course.id

    async def test_create_material_and_pipeline_run(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Create material + pipeline run in one transaction."""
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            teacher = _make_teacher(email="mat-run@ailine.dev")
            await uow.teachers.add(teacher)

            mat = MaterialRow(
                teacher_id=teacher.id,
                subject="Historia",
                title="Revolucao Francesa",
                content="A Revolucao Francesa foi...",
            )
            await uow.materials.add(mat)

            run = PipelineRunRow(
                teacher_id=teacher.id,
                input_json={"material_id": mat.id},
                status="pending",
            )
            await uow.pipeline_runs.add(run)
            await uow.commit()

        # Verify both exist
        async with session_factory() as verify_session:
            mat_stmt = select(MaterialRow).where(MaterialRow.teacher_id == teacher.id)
            mat_result = await verify_session.execute(mat_stmt)
            assert len(mat_result.scalars().all()) == 1

            run_stmt = select(PipelineRunRow).where(PipelineRunRow.teacher_id == teacher.id)
            run_result = await verify_session.execute(run_stmt)
            assert len(run_result.scalars().all()) == 1


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------


class TestSessionFactory:
    async def test_create_session_factory(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Session factory should create valid sessions."""
        async with session_factory() as session:
            assert session is not None
            # Verify expire_on_commit is False (attribute lives on sync_session)
            assert session.sync_session.expire_on_commit is False
