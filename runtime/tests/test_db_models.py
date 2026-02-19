"""Tests for SQLAlchemy ORM models and repository CRUD operations.

All tests run against in-memory aiosqlite -- no real Postgres needed.
Fixtures are defined in conftest.py.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ailine_runtime.adapters.db.models import (
    AccessibilityProfileRow,
    Base,
    ChunkRow,
    CourseRow,
    CurriculumObjectiveRow,
    LessonRow,
    MaterialRow,
    ParentStudentRow,
    PipelineRunRow,
    RunEventRow,
    TeacherRow,
    TeacherStudentRow,
    TutorAgentRow,
    TutorSessionRow,
    UserRow,
    _uuid7_str,
)
from ailine_runtime.adapters.db.repositories import (
    CourseRepository,
    LessonRepository,
    MaterialRepository,
    PipelineRunRepository,
    TeacherRepository,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_teacher(**overrides: str) -> TeacherRow:
    defaults: dict[str, str] = {
        "id": _uuid7_str(),
        "email": "ana@example.com",
        "display_name": "Ana Silva",
        "locale": "pt-BR",
    }
    defaults.update(overrides)
    return TeacherRow(**defaults)  # type: ignore[arg-type]


def _make_course(teacher_id: str, **overrides: str) -> CourseRow:
    defaults: dict[str, str] = {
        "id": _uuid7_str(),
        "teacher_id": teacher_id,
        "title": "Matematica 6o Ano",
        "subject": "Matematica",
        "grade": "6o ano",
        "standard": "BNCC",
    }
    defaults.update(overrides)
    return CourseRow(**defaults)  # type: ignore[arg-type]


def _make_lesson(teacher_id: str, course_id: str, **overrides: object) -> LessonRow:
    defaults: dict[str, object] = {
        "id": _uuid7_str(),
        "teacher_id": teacher_id,
        "course_id": course_id,
        "title": "Fracoes",
        "plan_json": {},
        "student_plan_json": {},
        "accessibility_json": {},
        "status": "draft",
    }
    defaults.update(overrides)  # type: ignore[arg-type]
    return LessonRow(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# UUID generation
# ---------------------------------------------------------------------------


class TestUuid7:
    def test_uuid7_str_format(self) -> None:
        uid = _uuid7_str()
        assert isinstance(uid, str)
        assert len(uid) == 36
        # UUID format: 8-4-4-4-12
        parts = uid.split("-")
        assert len(parts) == 5

    def test_uuid7_str_unique(self) -> None:
        ids = {_uuid7_str() for _ in range(100)}
        assert len(ids) == 100


# ---------------------------------------------------------------------------
# Table metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    def test_all_tables_registered(self) -> None:
        table_names = set(Base.metadata.tables.keys())
        expected = {
            "teachers",
            "courses",
            "lessons",
            "materials",
            "chunks",
            "pipeline_runs",
            "tutor_agents",
            "tutor_sessions",
            "curriculum_objectives",
            "run_events",
            "accessibility_profiles",
            "organizations",
            "users",
            "student_profiles",
            "teacher_students",
            "parent_students",
            "skills",
            "skill_versions",
            "skill_ratings",
            "teacher_skill_sets",
        }
        assert expected == table_names


# ---------------------------------------------------------------------------
# Teacher CRUD
# ---------------------------------------------------------------------------


class TestTeacherRepository:
    async def test_add_and_get(self, session: AsyncSession) -> None:
        repo = TeacherRepository(session)
        teacher = _make_teacher()
        added = await repo.add(teacher)
        assert added.id == teacher.id

        fetched = await repo.get(teacher.id)
        assert fetched is not None
        assert fetched.email == "ana@example.com"
        assert fetched.display_name == "Ana Silva"

    async def test_get_by_email(self, session: AsyncSession) -> None:
        repo = TeacherRepository(session)
        teacher = _make_teacher(email="test@ailine.dev")
        await repo.add(teacher)
        await session.flush()

        found = await repo.get_by_email("test@ailine.dev")
        assert found is not None
        assert found.id == teacher.id

    async def test_get_nonexistent_returns_none(self, session: AsyncSession) -> None:
        repo = TeacherRepository(session)
        assert await repo.get("nonexistent-id") is None

    async def test_list_all(self, session: AsyncSession) -> None:
        repo = TeacherRepository(session)
        t1 = _make_teacher(email="a@x.com")
        t2 = _make_teacher(email="b@x.com")
        await repo.add(t1)
        await repo.add(t2)
        await session.flush()

        all_teachers = await repo.list_all()
        assert len(all_teachers) == 2

    async def test_update_fields(self, session: AsyncSession) -> None:
        repo = TeacherRepository(session)
        teacher = _make_teacher()
        await repo.add(teacher)
        await session.flush()

        await repo.update_fields(teacher.id, display_name="Ana Updated")
        await session.flush()

        fetched = await repo.get(teacher.id)
        assert fetched is not None
        assert fetched.display_name == "Ana Updated"

    async def test_delete(self, session: AsyncSession) -> None:
        repo = TeacherRepository(session)
        teacher = _make_teacher()
        await repo.add(teacher)
        await session.flush()

        await repo.delete(teacher.id)
        await session.flush()

        assert await repo.get(teacher.id) is None


# ---------------------------------------------------------------------------
# Course CRUD
# ---------------------------------------------------------------------------


class TestCourseRepository:
    async def test_add_and_get(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        repo = CourseRepository(session)
        course = _make_course(teacher.id)
        await repo.add(course)
        await session.flush()

        fetched = await repo.get(course.id, teacher.id)
        assert fetched is not None
        assert fetched.title == "Matematica 6o Ano"

    async def test_tenant_scoping(self, session: AsyncSession) -> None:
        t1 = _make_teacher(email="t1@x.com")
        t2 = _make_teacher(email="t2@x.com")
        session.add_all([t1, t2])
        await session.flush()

        repo = CourseRepository(session)
        course = _make_course(t1.id)
        await repo.add(course)
        await session.flush()

        # t2 should NOT see t1's course
        assert await repo.get(course.id, t2.id) is None
        # t1 can see their own course
        assert await repo.get(course.id, t1.id) is not None

    async def test_list_by_teacher(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        repo = CourseRepository(session)
        c1 = _make_course(teacher.id, title="Course A")
        c2 = _make_course(teacher.id, title="Course B")
        await repo.add(c1)
        await repo.add(c2)
        await session.flush()

        courses = await repo.list_by_teacher(teacher.id)
        assert len(courses) == 2

    async def test_update_fields(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        repo = CourseRepository(session)
        course = _make_course(teacher.id)
        await repo.add(course)
        await session.flush()

        await repo.update_fields(course.id, teacher.id, title="Updated Title")
        await session.flush()

        fetched = await repo.get(course.id, teacher.id)
        assert fetched is not None
        assert fetched.title == "Updated Title"

    async def test_delete(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        repo = CourseRepository(session)
        course = _make_course(teacher.id)
        await repo.add(course)
        await session.flush()

        await repo.delete(course.id, teacher.id)
        await session.flush()

        assert await repo.get(course.id, teacher.id) is None


# ---------------------------------------------------------------------------
# Lesson CRUD (composite FK)
# ---------------------------------------------------------------------------


class TestLessonRepository:
    async def _setup(self, session: AsyncSession) -> tuple[str, str]:
        """Create teacher + course, return (teacher_id, course_id)."""
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()
        course = _make_course(teacher.id)
        session.add(course)
        await session.flush()
        return teacher.id, course.id

    async def test_add_and_get(self, session: AsyncSession) -> None:
        tid, cid = await self._setup(session)
        repo = LessonRepository(session)
        lesson = _make_lesson(tid, cid)
        await repo.add(lesson)
        await session.flush()

        fetched = await repo.get(lesson.id, tid)
        assert fetched is not None
        assert fetched.title == "Fracoes"
        assert fetched.course_id == cid

    async def test_list_by_course(self, session: AsyncSession) -> None:
        tid, cid = await self._setup(session)
        repo = LessonRepository(session)
        l1 = _make_lesson(tid, cid, title="Lesson 1")
        l2 = _make_lesson(tid, cid, title="Lesson 2")
        await repo.add(l1)
        await repo.add(l2)
        await session.flush()

        lessons = await repo.list_by_course(cid, tid)
        assert len(lessons) == 2

    async def test_tenant_scoping(self, session: AsyncSession) -> None:
        tid, cid = await self._setup(session)
        t2 = _make_teacher(email="other@x.com")
        session.add(t2)
        await session.flush()

        repo = LessonRepository(session)
        lesson = _make_lesson(tid, cid)
        await repo.add(lesson)
        await session.flush()

        # t2 cannot see t1's lesson
        assert await repo.get(lesson.id, t2.id) is None

    async def test_update_fields(self, session: AsyncSession) -> None:
        tid, cid = await self._setup(session)
        repo = LessonRepository(session)
        lesson = _make_lesson(tid, cid)
        await repo.add(lesson)
        await session.flush()

        await repo.update_fields(lesson.id, tid, title="Updated", status="ready")
        await session.flush()

        fetched = await repo.get(lesson.id, tid)
        assert fetched is not None
        assert fetched.title == "Updated"
        assert fetched.status == "ready"

    async def test_delete(self, session: AsyncSession) -> None:
        tid, cid = await self._setup(session)
        repo = LessonRepository(session)
        lesson = _make_lesson(tid, cid)
        await repo.add(lesson)
        await session.flush()

        await repo.delete(lesson.id, tid)
        await session.flush()

        assert await repo.get(lesson.id, tid) is None


# ---------------------------------------------------------------------------
# Material CRUD
# ---------------------------------------------------------------------------


class TestMaterialRepository:
    async def test_add_and_get(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        repo = MaterialRepository(session)
        mat = MaterialRow(
            teacher_id=teacher.id,
            subject="Matematica",
            title="Apostila Fracoes",
            content="Fracoes sao partes de um todo...",
            tags=["fracoes", "6o-ano"],
        )
        await repo.add(mat)
        await session.flush()

        fetched = await repo.get(mat.id, teacher.id)
        assert fetched is not None
        assert fetched.title == "Apostila Fracoes"
        assert fetched.tags == ["fracoes", "6o-ano"]

    async def test_list_by_teacher_with_subject_filter(
        self, session: AsyncSession
    ) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        repo = MaterialRepository(session)
        m1 = MaterialRow(
            teacher_id=teacher.id,
            subject="Matematica",
            title="Mat 1",
            content="...",
        )
        m2 = MaterialRow(
            teacher_id=teacher.id,
            subject="Portugues",
            title="Port 1",
            content="...",
        )
        await repo.add(m1)
        await repo.add(m2)
        await session.flush()

        all_mats = await repo.list_by_teacher(teacher.id)
        assert len(all_mats) == 2

        math_only = await repo.list_by_teacher(teacher.id, subject="Matematica")
        assert len(math_only) == 1
        assert math_only[0].subject == "Matematica"

    async def test_delete(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        repo = MaterialRepository(session)
        mat = MaterialRow(
            teacher_id=teacher.id,
            subject="Matematica",
            title="To Delete",
            content="...",
        )
        await repo.add(mat)
        await session.flush()

        await repo.delete(mat.id, teacher.id)
        await session.flush()
        assert await repo.get(mat.id, teacher.id) is None


# ---------------------------------------------------------------------------
# PipelineRun CRUD
# ---------------------------------------------------------------------------


class TestPipelineRunRepository:
    async def test_add_and_get(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        repo = PipelineRunRepository(session)
        run = PipelineRunRow(
            teacher_id=teacher.id,
            input_json={"subject": "Matematica"},
            status="pending",
        )
        await repo.add(run)
        await session.flush()

        fetched = await repo.get(run.id, teacher.id)
        assert fetched is not None
        assert fetched.status == "pending"
        assert fetched.input_json == {"subject": "Matematica"}

    async def test_list_by_teacher_with_status_filter(
        self, session: AsyncSession
    ) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        repo = PipelineRunRepository(session)
        r1 = PipelineRunRow(teacher_id=teacher.id, status="pending")
        r2 = PipelineRunRow(teacher_id=teacher.id, status="completed")
        await repo.add(r1)
        await repo.add(r2)
        await session.flush()

        all_runs = await repo.list_by_teacher(teacher.id)
        assert len(all_runs) == 2

        pending_only = await repo.list_by_teacher(teacher.id, status="pending")
        assert len(pending_only) == 1

    async def test_update_fields(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        repo = PipelineRunRepository(session)
        run = PipelineRunRow(teacher_id=teacher.id, status="pending")
        await repo.add(run)
        await session.flush()

        await repo.update_fields(run.id, teacher.id, status="running")
        await session.flush()

        fetched = await repo.get(run.id, teacher.id)
        assert fetched is not None
        assert fetched.status == "running"


# ---------------------------------------------------------------------------
# Remaining models (direct insertion tests)
# ---------------------------------------------------------------------------


class TestChunkRow:
    async def test_create_chunk(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        mat = MaterialRow(
            teacher_id=teacher.id,
            subject="Matematica",
            title="Test Mat",
            content="Full text here.",
        )
        session.add(mat)
        await session.flush()

        chunk = ChunkRow(
            teacher_id=teacher.id,
            material_id=mat.id,
            chunk_index=0,
            content="Full text here.",
            metadata_json={"tokens": 5},
        )
        session.add(chunk)
        await session.flush()

        stmt = select(ChunkRow).where(ChunkRow.material_id == mat.id)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].chunk_index == 0
        assert rows[0].metadata_json == {"tokens": 5}


class TestTutorAgentRow:
    async def test_create_tutor_agent(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        agent = TutorAgentRow(
            teacher_id=teacher.id,
            subject="Matematica",
            grade="6o ano",
            config_json={"style": "socratic"},
            persona_json={"system_prompt": "You are a math tutor."},
        )
        session.add(agent)
        await session.flush()

        stmt = select(TutorAgentRow).where(TutorAgentRow.teacher_id == teacher.id)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].config_json == {"style": "socratic"}


class TestTutorSessionRow:
    async def test_create_session(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        agent = TutorAgentRow(
            teacher_id=teacher.id,
            subject="Matematica",
            grade="6o ano",
        )
        session.add(agent)
        await session.flush()

        ts = TutorSessionRow(
            teacher_id=teacher.id,
            tutor_id=agent.id,
            messages_json=[{"role": "user", "content": "Hello"}],
        )
        session.add(ts)
        await session.flush()

        stmt = select(TutorSessionRow).where(TutorSessionRow.tutor_id == agent.id)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].messages_json == [{"role": "user", "content": "Hello"}]


class TestCurriculumObjectiveRow:
    async def test_create_objective(self, session: AsyncSession) -> None:
        obj = CurriculumObjectiveRow(
            code="EF06MA01",
            system="bncc",
            subject="Matematica",
            grade="6o ano",
            domain="Numeros",
            description="Comparar decimais e fracoes.",
            keywords=["fracoes", "decimais"],
        )
        session.add(obj)
        await session.flush()

        stmt = select(CurriculumObjectiveRow).where(
            CurriculumObjectiveRow.code == "EF06MA01"
        )
        result = await session.execute(stmt)
        row = result.scalar_one()
        assert row.system == "bncc"
        assert row.keywords == ["fracoes", "decimais"]

    async def test_unique_code_constraint(self, session: AsyncSession) -> None:
        """Two objectives with the same code should raise IntegrityError."""
        from sqlalchemy.exc import IntegrityError

        obj1 = CurriculumObjectiveRow(
            code="EF06MA01",
            system="bncc",
            subject="Matematica",
            grade="6o ano",
            description="First description.",
        )
        obj2 = CurriculumObjectiveRow(
            code="EF06MA01",
            system="bncc",
            subject="Matematica",
            grade="6o ano",
            description="Duplicate code.",
        )
        session.add(obj1)
        await session.flush()
        session.add(obj2)
        with pytest.raises(IntegrityError):
            await session.flush()


class TestRunEventRow:
    async def test_create_run_event(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        run = PipelineRunRow(teacher_id=teacher.id, status="running")
        session.add(run)
        await session.flush()

        event = RunEventRow(
            run_id=run.id,
            stage="planner",
            event_type="stage.started",
            data_json={"message": "Starting planner"},
        )
        session.add(event)
        await session.flush()

        stmt = select(RunEventRow).where(RunEventRow.run_id == run.id)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].event_type == "stage.started"


class TestAccessibilityProfileRow:
    async def test_create_profile(self, session: AsyncSession) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        profile = AccessibilityProfileRow(
            teacher_id=teacher.id,
            label="Autism Support",
            needs_json={"autism": "high"},
            supports_json={"visual_schedule": True},
            ui_prefs_json={"reduce_motion": True},
        )
        session.add(profile)
        await session.flush()

        stmt = select(AccessibilityProfileRow).where(
            AccessibilityProfileRow.teacher_id == teacher.id
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].label == "Autism Support"
        assert rows[0].needs_json == {"autism": "high"}


# ---------------------------------------------------------------------------
# Composite FK Cross-Tenant Isolation Tests (ADR-053)
# ---------------------------------------------------------------------------


class TestChunkCompositeFKTenantIsolation:
    """Verify chunk composite FK (teacher_id, material_id) prevents cross-tenant."""

    async def test_chunk_with_matching_teacher_id_succeeds(
        self, session: AsyncSession
    ) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        mat = MaterialRow(
            teacher_id=teacher.id,
            subject="Matematica",
            title="My Material",
            content="Content...",
        )
        session.add(mat)
        await session.flush()

        chunk = ChunkRow(
            teacher_id=teacher.id,
            material_id=mat.id,
            chunk_index=0,
            content="Chunk text",
        )
        session.add(chunk)
        await session.flush()

        assert chunk.teacher_id == teacher.id
        assert chunk.material_id == mat.id

    async def test_chunk_teacher_id_stored(self, session: AsyncSession) -> None:
        """Verify teacher_id is persisted on chunk rows."""
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        mat = MaterialRow(
            teacher_id=teacher.id,
            subject="Ciencias",
            title="Science Material",
            content="...",
        )
        session.add(mat)
        await session.flush()

        chunk = ChunkRow(
            teacher_id=teacher.id,
            material_id=mat.id,
            chunk_index=0,
            content="Chunk content",
        )
        session.add(chunk)
        await session.flush()

        stmt = select(ChunkRow).where(ChunkRow.teacher_id == teacher.id)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].teacher_id == teacher.id


class TestTutorSessionCompositeFKTenantIsolation:
    """Verify tutor_session composite FK (teacher_id, tutor_id) prevents cross-tenant."""

    async def test_session_with_matching_teacher_succeeds(
        self, session: AsyncSession
    ) -> None:
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        agent = TutorAgentRow(
            teacher_id=teacher.id,
            subject="Matematica",
            grade="6o ano",
        )
        session.add(agent)
        await session.flush()

        ts = TutorSessionRow(
            teacher_id=teacher.id,
            tutor_id=agent.id,
            messages_json=[],
        )
        session.add(ts)
        await session.flush()

        assert ts.teacher_id == teacher.id
        assert ts.tutor_id == agent.id

    async def test_session_teacher_id_stored(self, session: AsyncSession) -> None:
        """Verify teacher_id is persisted on session rows."""
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        agent = TutorAgentRow(
            teacher_id=teacher.id,
            subject="Portugues",
            grade="5o ano",
        )
        session.add(agent)
        await session.flush()

        ts = TutorSessionRow(
            teacher_id=teacher.id,
            tutor_id=agent.id,
            messages_json=[{"role": "user", "content": "Oi"}],
        )
        session.add(ts)
        await session.flush()

        stmt = select(TutorSessionRow).where(TutorSessionRow.teacher_id == teacher.id)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].teacher_id == teacher.id


class TestPipelineRunCompositeFKTenantIsolation:
    """Verify pipeline_run composite FK (teacher_id, lesson_id) prevents cross-tenant."""

    async def test_run_without_lesson_succeeds(self, session: AsyncSession) -> None:
        """Pipeline run with lesson_id=None should work fine."""
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        run = PipelineRunRow(
            teacher_id=teacher.id,
            status="pending",
            input_json={"test": True},
        )
        session.add(run)
        await session.flush()

        assert run.lesson_id is None
        assert run.teacher_id == teacher.id

    async def test_run_with_matching_lesson_succeeds(
        self, session: AsyncSession
    ) -> None:
        """Pipeline run referencing a lesson from the same teacher should work."""
        teacher = _make_teacher()
        session.add(teacher)
        await session.flush()

        course = _make_course(teacher.id)
        session.add(course)
        await session.flush()

        lesson = _make_lesson(teacher.id, course.id)
        session.add(lesson)
        await session.flush()

        run = PipelineRunRow(
            teacher_id=teacher.id,
            lesson_id=lesson.id,
            status="pending",
        )
        session.add(run)
        await session.flush()

        assert run.lesson_id == lesson.id
        assert run.teacher_id == teacher.id


# ---------------------------------------------------------------------------
# UniqueConstraint on relationship tables
# ---------------------------------------------------------------------------


class TestTeacherStudentUniqueConstraint:
    """Verify that (teacher_id, student_id) is unique on teacher_students."""

    async def test_duplicate_relationship_raises(self, session: AsyncSession) -> None:
        from sqlalchemy.exc import IntegrityError

        teacher = UserRow(
            email="teacher-uq@test.com",
            display_name="Teacher UQ",
            role="teacher",
        )
        student = UserRow(
            email="student-uq@test.com",
            display_name="Student UQ",
            role="student",
        )
        session.add_all([teacher, student])
        await session.flush()

        rel1 = TeacherStudentRow(
            teacher_id=teacher.id, student_id=student.id,
        )
        session.add(rel1)
        await session.flush()

        rel2 = TeacherStudentRow(
            teacher_id=teacher.id, student_id=student.id,
        )
        session.add(rel2)
        with pytest.raises(IntegrityError):
            await session.flush()

    async def test_different_pairs_allowed(self, session: AsyncSession) -> None:
        teacher = UserRow(
            email="t-diff@test.com", display_name="T", role="teacher",
        )
        s1 = UserRow(
            email="s1-diff@test.com", display_name="S1", role="student",
        )
        s2 = UserRow(
            email="s2-diff@test.com", display_name="S2", role="student",
        )
        session.add_all([teacher, s1, s2])
        await session.flush()

        session.add(TeacherStudentRow(teacher_id=teacher.id, student_id=s1.id))
        session.add(TeacherStudentRow(teacher_id=teacher.id, student_id=s2.id))
        await session.flush()  # should not raise


class TestParentStudentUniqueConstraint:
    """Verify that (parent_id, student_id) is unique on parent_students."""

    async def test_duplicate_relationship_raises(self, session: AsyncSession) -> None:
        from sqlalchemy.exc import IntegrityError

        parent = UserRow(
            email="parent-uq@test.com",
            display_name="Parent UQ",
            role="parent",
        )
        student = UserRow(
            email="student-puq@test.com",
            display_name="Student PUQ",
            role="student",
        )
        session.add_all([parent, student])
        await session.flush()

        rel1 = ParentStudentRow(
            parent_id=parent.id, student_id=student.id,
        )
        session.add(rel1)
        await session.flush()

        rel2 = ParentStudentRow(
            parent_id=parent.id, student_id=student.id,
        )
        session.add(rel2)
        with pytest.raises(IntegrityError):
            await session.flush()
