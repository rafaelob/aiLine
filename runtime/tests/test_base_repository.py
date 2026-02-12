"""Tests for FINDING-03: Generic BaseRepository[T] pattern."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ailine_runtime.adapters.db.models import (
    CourseRow,
    MaterialRow,
    PipelineRunRow,
    TeacherRow,
)
from ailine_runtime.adapters.db.repositories import (
    BaseRepository,
    CourseRepository,
    LessonRepository,
    MaterialRepository,
    PipelineRunRepository,
    TeacherRepository,
)


class TestBaseRepositoryInheritance:
    def test_course_repo_inherits_base(self):
        assert issubclass(CourseRepository, BaseRepository)

    def test_lesson_repo_inherits_base(self):
        assert issubclass(LessonRepository, BaseRepository)

    def test_material_repo_inherits_base(self):
        assert issubclass(MaterialRepository, BaseRepository)

    def test_pipeline_run_repo_inherits_base(self):
        assert issubclass(PipelineRunRepository, BaseRepository)

    def test_teacher_repo_does_not_inherit_base(self):
        """Teacher is the tenant root, no teacher_id scoping on itself."""
        assert not issubclass(TeacherRepository, BaseRepository)


class TestBaseRepositoryCRUD:
    @pytest.mark.asyncio
    async def test_course_crud_via_base(self, session: AsyncSession):
        teacher = TeacherRow(email="t@test.com", display_name="Teacher")
        session.add(teacher)
        await session.flush()

        repo = CourseRepository(session)
        course = CourseRow(
            teacher_id=teacher.id,
            title="Math",
            subject="Mathematics",
            grade="6th",
        )
        added = await repo.add(course)
        assert added.id is not None

        # get via base method
        fetched = await repo.get_by_id_and_teacher(added.id, teacher.id)
        assert fetched is not None
        assert fetched.title == "Math"

        # get via convenience method
        fetched2 = await repo.get(added.id, teacher.id)
        assert fetched2 is not None
        assert fetched2.id == added.id

        # list_by_teacher via base
        courses = await repo.list_by_teacher(teacher.id)
        assert len(courses) == 1

        # update via base
        await repo.update_fields(added.id, teacher.id, title="Advanced Math")
        await session.flush()
        updated = await repo.get(added.id, teacher.id)
        assert updated is not None
        assert updated.title == "Advanced Math"

        # delete via base
        await repo.delete(added.id, teacher.id)
        await session.flush()
        deleted = await repo.get(added.id, teacher.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_tenant_scoping_prevents_cross_tenant_access(self, session: AsyncSession):
        t1 = TeacherRow(email="t1@test.com", display_name="Teacher 1")
        t2 = TeacherRow(email="t2@test.com", display_name="Teacher 2")
        session.add_all([t1, t2])
        await session.flush()

        repo = CourseRepository(session)
        course = CourseRow(
            teacher_id=t1.id,
            title="T1 Course",
            subject="Math",
            grade="6th",
        )
        await repo.add(course)

        # T2 cannot see T1's course
        result = await repo.get(course.id, t2.id)
        assert result is None

        # T2 list is empty
        t2_courses = await repo.list_by_teacher(t2.id)
        assert len(t2_courses) == 0

    @pytest.mark.asyncio
    async def test_get_by_id_no_tenant(self, session: AsyncSession):
        """get_by_id (no tenant scoping) works for admin scenarios."""
        teacher = TeacherRow(email="admin@test.com", display_name="Admin")
        session.add(teacher)
        await session.flush()

        repo = CourseRepository(session)
        course = CourseRow(
            teacher_id=teacher.id,
            title="Admin View",
            subject="Science",
            grade="7th",
        )
        await repo.add(course)

        # get_by_id does NOT scope by teacher
        fetched = await repo.get_by_id(course.id)
        assert fetched is not None
        assert fetched.title == "Admin View"

    @pytest.mark.asyncio
    async def test_material_repo_crud(self, session: AsyncSession):
        teacher = TeacherRow(email="mat@test.com", display_name="Teacher")
        session.add(teacher)
        await session.flush()

        repo = MaterialRepository(session)
        mat = MaterialRow(
            teacher_id=teacher.id,
            subject="History",
            title="World War II",
            content="Content about WWII",
        )
        added = await repo.add(mat)
        assert added.id is not None

        fetched = await repo.get(added.id, teacher.id)
        assert fetched is not None

        materials = await repo.list_by_teacher(teacher.id, subject="History")
        assert len(materials) == 1

        await repo.delete(added.id, teacher.id)
        await session.flush()
        assert await repo.get(added.id, teacher.id) is None

    @pytest.mark.asyncio
    async def test_pipeline_run_repo_crud(self, session: AsyncSession):
        teacher = TeacherRow(email="pr@test.com", display_name="Teacher")
        session.add(teacher)
        await session.flush()

        repo = PipelineRunRepository(session)
        run = PipelineRunRow(teacher_id=teacher.id, status="pending")
        added = await repo.add(run)

        fetched = await repo.get(added.id, teacher.id)
        assert fetched is not None
        assert fetched.status == "pending"

        await repo.update_fields(added.id, teacher.id, status="completed")
        await session.flush()
        updated = await repo.get(added.id, teacher.id)
        assert updated is not None
        assert updated.status == "completed"

        runs = await repo.list_by_teacher(teacher.id, status="completed")
        assert len(runs) == 1
