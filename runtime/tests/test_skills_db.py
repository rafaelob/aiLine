"""Tests for the Skills DB persistence layer (F-175).

Covers:
- SkillRow / SkillVersionRow / SkillRatingRow / TeacherSkillSetRow ORM mapping
- Domain entity round-trips (Skill <-> SkillRow)
- FakeSkillRepository CRUD
- PostgresSkillRepository CRUD (via aiosqlite in-memory)
- Search, fork, rate operations
- Unique constraint enforcement
- SkillRepository protocol conformance
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ailine_runtime.adapters.db.fake_skill_repository import FakeSkillRepository
from ailine_runtime.adapters.db.models import (
    Base,
    SkillRatingRow,
    SkillRow,
    SkillVersionRow,
    TeacherSkillSetRow,
    UserRow,
    _uuid7_str,
)
from ailine_runtime.adapters.db.skill_repository import (
    PostgresSkillRepository,
    _row_to_skill,
)
from ailine_runtime.domain.entities.skill import Skill, SkillRating, SkillVersion
from ailine_runtime.domain.ports.skills import SkillRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_skill(slug: str = "lesson-planner", **overrides: object) -> Skill:
    defaults: dict[str, object] = {
        "slug": slug,
        "description": "Plans lessons effectively.",
        "instructions_md": "# Lesson Planner\nCreate detailed lesson plans.",
        "metadata": {"category": "planning"},
        "license": "MIT",
        "compatibility": "pydantic-ai",
        "allowed_tools": "web_search file_read",
    }
    defaults.update(overrides)
    return Skill(**defaults)  # type: ignore[arg-type]


def _make_user(session: AsyncSession, **overrides: str) -> UserRow:
    defaults = {
        "email": f"user-{_uuid7_str()[:8]}@test.com",
        "display_name": "Test User",
        "role": "teacher",
    }
    defaults.update(overrides)
    user = UserRow(**defaults)  # type: ignore[arg-type]
    session.add(user)
    return user


# ---------------------------------------------------------------------------
# ORM Model Tests — SkillRow
# ---------------------------------------------------------------------------


class TestSkillRowORM:
    """Verify SkillRow ORM mapping and basic CRUD."""

    async def test_create_skill_row(self, session: AsyncSession) -> None:
        row = SkillRow(
            slug="quiz-generator",
            description="Generates quizzes.",
            instructions_md="# Quiz Gen\nBuild quizzes.",
            metadata_json={"category": "assessment"},
            is_system=True,
        )
        session.add(row)
        await session.flush()

        stmt = select(SkillRow).where(SkillRow.slug == "quiz-generator")
        result = await session.execute(stmt)
        fetched = result.scalar_one()
        assert fetched.slug == "quiz-generator"
        assert fetched.description == "Generates quizzes."
        assert fetched.is_system is True
        assert fetched.is_active is True
        assert fetched.version == 1
        assert fetched.avg_rating == 0.0
        assert fetched.rating_count == 0
        assert fetched.metadata_json == {"category": "assessment"}

    async def test_skill_slug_uniqueness(self, session: AsyncSession) -> None:
        # The unique constraint is composite (teacher_id, slug).
        # Use the same teacher_id so the constraint fires.
        user = _make_user(session)
        await session.flush()
        row1 = SkillRow(
            slug="unique-skill",
            description="First",
            instructions_md="A",
            teacher_id=user.id,
        )
        row2 = SkillRow(
            slug="unique-skill",
            description="Second",
            instructions_md="B",
            teacher_id=user.id,
        )
        session.add(row1)
        await session.flush()
        session.add(row2)
        with pytest.raises(IntegrityError):
            await session.flush()

    async def test_skill_with_user_fk(self, session: AsyncSession) -> None:
        user = _make_user(session)
        await session.flush()

        row = SkillRow(
            slug="teacher-skill",
            description="Custom skill",
            instructions_md="# Custom",
            teacher_id=user.id,
        )
        session.add(row)
        await session.flush()

        stmt = select(SkillRow).where(SkillRow.slug == "teacher-skill")
        result = await session.execute(stmt)
        fetched = result.scalar_one()
        assert fetched.teacher_id == user.id

    async def test_skill_self_reference_fork(self, session: AsyncSession) -> None:
        parent = SkillRow(
            slug="parent-skill",
            description="Parent",
            instructions_md="# Parent",
        )
        session.add(parent)
        await session.flush()

        child = SkillRow(
            slug="child-skill",
            description="Child",
            instructions_md="# Child",
            forked_from_id=parent.id,
        )
        session.add(child)
        await session.flush()

        stmt = select(SkillRow).where(SkillRow.slug == "child-skill")
        result = await session.execute(stmt)
        fetched = result.scalar_one()
        assert fetched.forked_from_id == parent.id


# ---------------------------------------------------------------------------
# ORM Model Tests — SkillVersionRow
# ---------------------------------------------------------------------------


class TestSkillVersionRowORM:
    async def test_create_version(self, session: AsyncSession) -> None:
        skill = SkillRow(
            slug="versioned-skill",
            description="V",
            instructions_md="# V1",
        )
        session.add(skill)
        await session.flush()

        v1 = SkillVersionRow(
            skill_id=skill.id,
            version=1,
            instructions_md="# V1",
            metadata_json={"rev": "initial"},
            change_summary="Initial version",
        )
        session.add(v1)
        await session.flush()

        stmt = select(SkillVersionRow).where(
            SkillVersionRow.skill_id == skill.id
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].version == 1
        assert rows[0].change_summary == "Initial version"

    async def test_version_uniqueness(self, session: AsyncSession) -> None:
        skill = SkillRow(
            slug="dup-version-skill",
            description="D",
            instructions_md="# D",
        )
        session.add(skill)
        await session.flush()

        v1a = SkillVersionRow(
            skill_id=skill.id, version=1, instructions_md="A",
        )
        v1b = SkillVersionRow(
            skill_id=skill.id, version=1, instructions_md="B",
        )
        session.add(v1a)
        await session.flush()
        session.add(v1b)
        with pytest.raises(IntegrityError):
            await session.flush()


# ---------------------------------------------------------------------------
# ORM Model Tests — SkillRatingRow
# ---------------------------------------------------------------------------


class TestSkillRatingRowORM:
    async def test_create_rating(self, session: AsyncSession) -> None:
        user = _make_user(session)
        await session.flush()

        skill = SkillRow(
            slug="rated-skill",
            description="R",
            instructions_md="# R",
        )
        session.add(skill)
        await session.flush()

        rating = SkillRatingRow(
            skill_id=skill.id,
            user_id=user.id,
            score=5,
            comment="Excellent!",
        )
        session.add(rating)
        await session.flush()

        stmt = select(SkillRatingRow).where(
            SkillRatingRow.skill_id == skill.id
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].score == 5
        assert rows[0].comment == "Excellent!"

    async def test_rating_uniqueness_per_user(self, session: AsyncSession) -> None:
        user = _make_user(session)
        await session.flush()

        skill = SkillRow(
            slug="dup-rate-skill",
            description="DR",
            instructions_md="# DR",
        )
        session.add(skill)
        await session.flush()

        r1 = SkillRatingRow(skill_id=skill.id, user_id=user.id, score=4)
        r2 = SkillRatingRow(skill_id=skill.id, user_id=user.id, score=3)
        session.add(r1)
        await session.flush()
        session.add(r2)
        with pytest.raises(IntegrityError):
            await session.flush()


# ---------------------------------------------------------------------------
# ORM Model Tests — TeacherSkillSetRow
# ---------------------------------------------------------------------------


class TestTeacherSkillSetRowORM:
    async def test_create_skill_set(self, session: AsyncSession) -> None:
        user = _make_user(session)
        await session.flush()

        ss = TeacherSkillSetRow(
            teacher_id=user.id,
            name="My Favorites",
            description="Top skills",
            skill_slugs_json=["lesson-planner", "quiz-generator"],
            is_default=True,
        )
        session.add(ss)
        await session.flush()

        stmt = select(TeacherSkillSetRow).where(
            TeacherSkillSetRow.teacher_id == user.id
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        assert len(rows) == 1
        assert rows[0].name == "My Favorites"
        assert rows[0].skill_slugs_json == ["lesson-planner", "quiz-generator"]
        assert rows[0].is_default is True

    async def test_skill_set_name_uniqueness(self, session: AsyncSession) -> None:
        user = _make_user(session)
        await session.flush()

        ss1 = TeacherSkillSetRow(
            teacher_id=user.id, name="Same Name", skill_slugs_json=[],
        )
        ss2 = TeacherSkillSetRow(
            teacher_id=user.id, name="Same Name", skill_slugs_json=[],
        )
        session.add(ss1)
        await session.flush()
        session.add(ss2)
        with pytest.raises(IntegrityError):
            await session.flush()

    async def test_different_teachers_same_name_allowed(
        self, session: AsyncSession
    ) -> None:
        u1 = _make_user(session, email="t1-ss@test.com")
        u2 = _make_user(session, email="t2-ss@test.com")
        await session.flush()

        ss1 = TeacherSkillSetRow(
            teacher_id=u1.id, name="Default", skill_slugs_json=[],
        )
        ss2 = TeacherSkillSetRow(
            teacher_id=u2.id, name="Default", skill_slugs_json=[],
        )
        session.add_all([ss1, ss2])
        await session.flush()  # Should not raise


# ---------------------------------------------------------------------------
# Domain Entity Round-Trip
# ---------------------------------------------------------------------------


class TestSkillEntityRoundTrip:
    async def test_row_to_skill(self, session: AsyncSession) -> None:
        row = SkillRow(
            slug="round-trip",
            description="Test round trip",
            instructions_md="# RT",
            metadata_json={"k": "v"},
            license="MIT",
            compatibility="pydantic-ai",
            allowed_tools="web_search",
            is_system=True,
            version=3,
            avg_rating=4.5,
            rating_count=10,
        )
        session.add(row)
        await session.flush()

        skill = _row_to_skill(row)
        assert skill.slug == "round-trip"
        assert skill.description == "Test round trip"
        assert skill.instructions_md == "# RT"
        assert skill.metadata == {"k": "v"}
        assert skill.license == "MIT"
        assert skill.is_system is True
        assert skill.version == 3
        assert skill.avg_rating == 4.5
        assert skill.rating_count == 10

    def test_skill_entity_creation(self) -> None:
        skill = _make_skill()
        assert skill.slug == "lesson-planner"
        assert skill.description == "Plans lessons effectively."
        assert skill.version == 1
        assert skill.is_active is True

    def test_skill_version_entity(self) -> None:
        sv = SkillVersion(
            skill_id="abc", version=2, instructions_md="# Updated",
            change_summary="Changed intro",
        )
        assert sv.version == 2
        assert sv.change_summary == "Changed intro"

    def test_skill_rating_entity(self) -> None:
        sr = SkillRating(
            skill_id="abc", user_id="user1", score=4, comment="Good",
        )
        assert sr.score == 4
        assert sr.comment == "Good"


# ---------------------------------------------------------------------------
# Table Metadata (extended check)
# ---------------------------------------------------------------------------


class TestSkillsTableMetadata:
    def test_skills_tables_registered(self) -> None:
        table_names = set(Base.metadata.tables.keys())
        assert "skills" in table_names
        assert "skill_versions" in table_names
        assert "skill_ratings" in table_names
        assert "teacher_skill_sets" in table_names


# ---------------------------------------------------------------------------
# FakeSkillRepository Tests
# ---------------------------------------------------------------------------


class TestFakeSkillRepository:
    @pytest.fixture()
    def repo(self) -> FakeSkillRepository:
        return FakeSkillRepository()

    async def test_create_and_get(self, repo: FakeSkillRepository) -> None:
        skill = _make_skill()
        skill_id = await repo.create(skill, is_system=True)
        assert skill_id

        fetched = await repo.get_by_slug("lesson-planner")
        assert fetched is not None
        assert fetched.slug == "lesson-planner"
        assert fetched.is_system is True

    async def test_get_nonexistent_returns_none(
        self, repo: FakeSkillRepository
    ) -> None:
        assert await repo.get_by_slug("nonexistent") is None

    async def test_list_all(self, repo: FakeSkillRepository) -> None:
        await repo.create(_make_skill("skill-a"))
        await repo.create(_make_skill("skill-b"))
        all_skills = await repo.list_all()
        assert len(all_skills) == 2

    async def test_list_all_system_only(self, repo: FakeSkillRepository) -> None:
        await repo.create(_make_skill("system"), is_system=True)
        await repo.create(_make_skill("custom"), is_system=False)
        system = await repo.list_all(system_only=True)
        assert len(system) == 1
        assert system[0].slug == "system"

    async def test_update_increments_version(
        self, repo: FakeSkillRepository
    ) -> None:
        await repo.create(_make_skill())
        await repo.update("lesson-planner", description="Updated desc")
        skill = await repo.get_by_slug("lesson-planner")
        assert skill is not None
        assert skill.description == "Updated desc"
        assert skill.version == 2

    async def test_soft_delete(self, repo: FakeSkillRepository) -> None:
        await repo.create(_make_skill())
        await repo.soft_delete("lesson-planner")
        assert await repo.get_by_slug("lesson-planner") is None

    async def test_search_by_text(self, repo: FakeSkillRepository) -> None:
        await repo.create(_make_skill("quiz-generator", description="Generates quizzes"))
        await repo.create(_make_skill("lesson-planner", description="Plans lessons"))
        results = await repo.search_by_text("quiz")
        assert len(results) == 1
        assert results[0].slug == "quiz-generator"

    async def test_list_by_teacher(self, repo: FakeSkillRepository) -> None:
        await repo.create(_make_skill("t1-skill"), teacher_id="teacher-1")
        await repo.create(_make_skill("t2-skill"), teacher_id="teacher-2")
        t1_skills = await repo.list_by_teacher("teacher-1")
        assert len(t1_skills) == 1
        assert t1_skills[0].slug == "t1-skill"

    async def test_fork(self, repo: FakeSkillRepository) -> None:
        await repo.create(_make_skill("source-skill"))
        forked_id = await repo.fork("source-skill", teacher_id="teacher-abc")
        assert forked_id

        forked = await repo.get_by_slug("source-skill-fork")
        assert forked is not None
        assert forked.forked_from_id is not None
        assert forked.teacher_id == "teacher-abc"

    async def test_fork_nonexistent_raises(
        self, repo: FakeSkillRepository
    ) -> None:
        with pytest.raises(ValueError, match="not found"):
            await repo.fork("nonexistent", teacher_id="t1")

    async def test_rate(self, repo: FakeSkillRepository) -> None:
        await repo.create(_make_skill())
        await repo.rate("lesson-planner", user_id="user-1", score=5)
        skill = await repo.get_by_slug("lesson-planner")
        assert skill is not None
        assert skill.avg_rating == 5.0
        assert skill.rating_count == 1

    async def test_rate_multiple_users_average(
        self, repo: FakeSkillRepository
    ) -> None:
        await repo.create(_make_skill())
        await repo.rate("lesson-planner", user_id="u1", score=4)
        await repo.rate("lesson-planner", user_id="u2", score=2)
        skill = await repo.get_by_slug("lesson-planner")
        assert skill is not None
        assert skill.avg_rating == 3.0
        assert skill.rating_count == 2

    async def test_protocol_conformance(self) -> None:
        assert isinstance(FakeSkillRepository(), SkillRepository)


# ---------------------------------------------------------------------------
# PostgresSkillRepository Tests (aiosqlite in-memory)
# ---------------------------------------------------------------------------


class TestPostgresSkillRepository:
    @pytest.fixture()
    def repo(self, session: AsyncSession) -> PostgresSkillRepository:
        return PostgresSkillRepository(session)

    async def test_create_and_get(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        skill = _make_skill()
        skill_id = await repo.create(skill, is_system=True)
        assert skill_id

        fetched = await repo.get_by_slug("lesson-planner")
        assert fetched is not None
        assert fetched.slug == "lesson-planner"
        assert fetched.is_system is True
        assert fetched.version == 1

    async def test_create_generates_initial_version(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        skill = _make_skill()
        skill_id = await repo.create(skill)

        stmt = select(SkillVersionRow).where(
            SkillVersionRow.skill_id == skill_id
        )
        result = await session.execute(stmt)
        versions = result.scalars().all()
        assert len(versions) == 1
        assert versions[0].version == 1
        assert versions[0].change_summary == "Initial version"

    async def test_get_nonexistent(
        self, repo: PostgresSkillRepository
    ) -> None:
        assert await repo.get_by_slug("nonexistent") is None

    async def test_list_all(
        self, repo: PostgresSkillRepository
    ) -> None:
        await repo.create(_make_skill("skill-a"))
        await repo.create(_make_skill("skill-b"))
        all_skills = await repo.list_all()
        assert len(all_skills) == 2
        slugs = [s.slug for s in all_skills]
        assert "skill-a" in slugs
        assert "skill-b" in slugs

    async def test_list_all_active_only(
        self, repo: PostgresSkillRepository
    ) -> None:
        await repo.create(_make_skill("active-skill"))
        await repo.create(_make_skill("deleted-skill"))
        await repo.soft_delete("deleted-skill")
        active = await repo.list_all(active_only=True)
        slugs = [s.slug for s in active]
        assert "active-skill" in slugs
        assert "deleted-skill" not in slugs

    async def test_list_all_system_only(
        self, repo: PostgresSkillRepository
    ) -> None:
        await repo.create(_make_skill("system-s"), is_system=True)
        await repo.create(_make_skill("custom-s"), is_system=False)
        system = await repo.list_all(system_only=True)
        assert len(system) == 1
        assert system[0].slug == "system-s"

    async def test_update_creates_new_version(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        skill = _make_skill()
        skill_id = await repo.create(skill)

        await repo.update(
            "lesson-planner",
            description="Updated description",
            change_summary="Improved wording",
        )

        fetched = await repo.get_by_slug("lesson-planner")
        assert fetched is not None
        assert fetched.description == "Updated description"
        assert fetched.version == 2

        stmt = select(SkillVersionRow).where(
            SkillVersionRow.skill_id == skill_id
        ).order_by(SkillVersionRow.version)
        result = await session.execute(stmt)
        versions = result.scalars().all()
        assert len(versions) == 2
        assert versions[1].version == 2
        assert versions[1].change_summary == "Improved wording"

    async def test_update_nonexistent_is_noop(
        self, repo: PostgresSkillRepository
    ) -> None:
        await repo.update("nonexistent", description="Should not fail")

    async def test_soft_delete(
        self, repo: PostgresSkillRepository
    ) -> None:
        await repo.create(_make_skill())
        await repo.soft_delete("lesson-planner")
        assert await repo.get_by_slug("lesson-planner") is None

        # Still in DB, just inactive
        all_including_inactive = await repo.list_all(active_only=False)
        slugs = [s.slug for s in all_including_inactive]
        assert "lesson-planner" in slugs

    async def test_search_by_text(
        self, repo: PostgresSkillRepository
    ) -> None:
        await repo.create(
            _make_skill("quiz-generator", description="Generates quizzes for students")
        )
        await repo.create(
            _make_skill("lesson-planner", description="Plans detailed lessons")
        )

        results = await repo.search_by_text("quiz")
        assert len(results) == 1
        assert results[0].slug == "quiz-generator"

    async def test_search_by_text_in_slug(
        self, repo: PostgresSkillRepository
    ) -> None:
        await repo.create(_make_skill("socratic-tutor", description="Tutoring"))
        results = await repo.search_by_text("socratic")
        assert len(results) == 1

    async def test_list_by_teacher(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        u1 = _make_user(session, email="teacher-1@test.com")
        u2 = _make_user(session, email="teacher-2@test.com")
        await session.flush()

        await repo.create(_make_skill("t1-skill"), teacher_id=u1.id)
        await repo.create(_make_skill("t2-skill"), teacher_id=u2.id)

        t1_skills = await repo.list_by_teacher(u1.id)
        assert len(t1_skills) == 1
        assert t1_skills[0].slug == "t1-skill"

    async def test_fork(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        user = _make_user(session)
        await session.flush()

        await repo.create(_make_skill("source-skill"), is_system=True)
        forked_id = await repo.fork("source-skill", teacher_id=user.id)
        assert forked_id

        # Forked skill should exist with teacher ownership
        forked = await repo.get_by_slug("source-skill-fork")
        assert forked is not None
        assert forked.teacher_id == user.id
        assert forked.forked_from_id is not None
        assert forked.is_system is False

    async def test_fork_creates_version_snapshot(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        user = _make_user(session)
        await session.flush()

        await repo.create(_make_skill("fork-source"), is_system=True)
        forked_id = await repo.fork("fork-source", teacher_id=user.id)

        stmt = select(SkillVersionRow).where(
            SkillVersionRow.skill_id == forked_id
        )
        result = await session.execute(stmt)
        versions = result.scalars().all()
        assert len(versions) == 1
        assert "Forked from" in versions[0].change_summary

    async def test_fork_nonexistent_raises(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        user = _make_user(session)
        await session.flush()

        with pytest.raises(ValueError, match="not found"):
            await repo.fork("nonexistent", teacher_id=user.id)

    async def test_rate_skill(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        user = _make_user(session)
        await session.flush()

        await repo.create(_make_skill())
        await repo.rate("lesson-planner", user_id=user.id, score=5, comment="Great!")

        skill = await repo.get_by_slug("lesson-planner")
        assert skill is not None
        assert skill.avg_rating == 5.0
        assert skill.rating_count == 1

    async def test_rate_upsert(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        user = _make_user(session)
        await session.flush()

        await repo.create(_make_skill())
        await repo.rate("lesson-planner", user_id=user.id, score=5)
        await repo.rate("lesson-planner", user_id=user.id, score=3)

        skill = await repo.get_by_slug("lesson-planner")
        assert skill is not None
        assert skill.avg_rating == 3.0
        assert skill.rating_count == 1

    async def test_rate_multiple_users(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        u1 = _make_user(session, email="rater1@test.com")
        u2 = _make_user(session, email="rater2@test.com")
        await session.flush()

        await repo.create(_make_skill())
        await repo.rate("lesson-planner", user_id=u1.id, score=4)
        await repo.rate("lesson-planner", user_id=u2.id, score=2)

        skill = await repo.get_by_slug("lesson-planner")
        assert skill is not None
        assert skill.avg_rating == 3.0
        assert skill.rating_count == 2

    async def test_search_similar_graceful_fallback(
        self, repo: PostgresSkillRepository
    ) -> None:
        # In aiosqlite, vector search is not supported -- should return empty
        result = await repo.search_similar([0.1] * 1536)
        assert result == []

    async def test_update_embedding_graceful(
        self, repo: PostgresSkillRepository
    ) -> None:
        # Should not raise even on non-Postgres backends
        await repo.create(_make_skill())
        await repo.update_embedding("lesson-planner", [0.1] * 1536)

    async def test_create_with_teacher_id(
        self, repo: PostgresSkillRepository, session: AsyncSession
    ) -> None:
        user = _make_user(session)
        await session.flush()

        await repo.create(
            _make_skill("teacher-custom"),
            teacher_id=user.id,
            is_system=False,
        )
        fetched = await repo.get_by_slug("teacher-custom")
        assert fetched is not None
        assert fetched.teacher_id == user.id
        assert fetched.is_system is False
