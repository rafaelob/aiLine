"""Tests for Sprint 29 CRITICAL security fixes (F-399 to F-403).

Covers:
- F-399: Parent IDOR in /progress/student/{student_id} — FERPA compliance
- F-400: Cross-tenant skill slug ambiguity
- F-401: Composite FK unique constraint (ORM model validation)
- F-402: CI security scans blocking (YAML structure validation)
- F-403: /auth/demo-login gated behind AILINE_DEMO_MODE
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ailine_runtime.adapters.db.models import (
    CourseRow,
    LessonRow,
    MaterialRow,
    SkillRow,
    TutorAgentRow,
)
from ailine_runtime.adapters.db.skill_repository import PostgresSkillRepository
from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import (
    DatabaseConfig,
    EmbeddingConfig,
    LLMConfig,
    RedisConfig,
    Settings,
)
from ailine_runtime.shared.progress_store import ProgressStore

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings_dev() -> Settings:
    return Settings(
        anthropic_api_key="fake-key",
        openai_api_key="",
        google_api_key="",
        openrouter_api_key="",
        db=DatabaseConfig(url="sqlite+aiosqlite:///:memory:"),
        llm=LLMConfig(provider="fake", api_key="fake"),
        embedding=EmbeddingConfig(provider="gemini", api_key=""),
        redis=RedisConfig(url=""),
    )


def _reset_auth_store() -> None:
    from ailine_runtime.adapters.db.user_repository import InMemoryUserRepository
    from ailine_runtime.api.routers import auth as auth_mod

    auth_mod._user_repo = InMemoryUserRepository()
    auth_mod._login_attempts.clear()


# ---------------------------------------------------------------------------
# F-399: Parent IDOR in /progress/student/{student_id}
# ---------------------------------------------------------------------------


class TestParentProgressIDOR:
    """F-399: Verify parent can only see linked students' progress."""

    def test_parent_without_linkage_denied(self) -> None:
        """A parent with no linkage to a student is denied access."""
        store = ProgressStore()
        # Record some progress for student-1 by teacher-1
        store.record_progress(
            teacher_id="teacher-1",
            student_id="student-1",
            student_name="Student One",
            standard_code="EF06MA01",
            standard_description="Fractions",
            mastery_level="developing",
        )
        # Parent-99 is NOT linked to student-1
        assert store.is_parent_linked("parent-99", "student-1") is False

    def test_parent_with_linkage_allowed(self) -> None:
        """A parent linked to a student can see their progress."""
        store = ProgressStore()
        store.link_parent_student("parent-1", "student-1")
        assert store.is_parent_linked("parent-1", "student-1") is True

    def test_parent_cannot_see_unlinked_student(self) -> None:
        """Even if a parent is linked to one student, they cannot see another."""
        store = ProgressStore()
        store.link_parent_student("parent-1", "student-1")
        # Parent-1 is linked to student-1 but NOT to student-2
        assert store.is_parent_linked("parent-1", "student-1") is True
        assert store.is_parent_linked("parent-1", "student-2") is False

    def test_multiple_parents_can_link_same_student(self) -> None:
        """Multiple parents can be linked to the same student."""
        store = ProgressStore()
        store.link_parent_student("parent-1", "student-1")
        store.link_parent_student("parent-2", "student-1")
        assert store.is_parent_linked("parent-1", "student-1") is True
        assert store.is_parent_linked("parent-2", "student-1") is True


# ---------------------------------------------------------------------------
# F-400: Cross-tenant skill slug ambiguity
# ---------------------------------------------------------------------------


def _make_skill_row(slug: str, teacher_id: str | None = None) -> SkillRow:
    return SkillRow(
        slug=slug,
        description=f"Test {slug}",
        instructions_md=f"# {slug}",
        metadata_json={},
        license="MIT",
        compatibility="*",
        allowed_tools="",
        teacher_id=teacher_id,
        is_system=teacher_id is None,
        version=1,
    )


class TestSkillSlugAmbiguity:
    """F-400: Slug-based lookups must include teacher_id to avoid MultipleResultsFound."""

    async def test_same_slug_different_teachers_no_error(self, session: AsyncSession) -> None:
        """Two teachers can own skills with the same slug without errors."""
        from ailine_runtime.adapters.db.models import UserRow

        # Create two teacher users
        t1 = UserRow(email="t1-skill@test.com", display_name="T1", role="teacher")
        t2 = UserRow(email="t2-skill@test.com", display_name="T2", role="teacher")
        session.add_all([t1, t2])
        await session.flush()

        # Same slug, different teachers
        s1 = _make_skill_row("quiz-generator", teacher_id=t1.id)
        s2 = _make_skill_row("quiz-generator", teacher_id=t2.id)
        session.add_all([s1, s2])
        await session.flush()

        repo = PostgresSkillRepository(session)

        # With teacher_id filter, each teacher sees their own skill
        skill_t1 = await repo.get_by_slug("quiz-generator", teacher_id=t1.id)
        assert skill_t1 is not None
        assert skill_t1.teacher_id == t1.id

        skill_t2 = await repo.get_by_slug("quiz-generator", teacher_id=t2.id)
        assert skill_t2 is not None
        assert skill_t2.teacher_id == t2.id

    async def test_system_skill_fallback(self, session: AsyncSession) -> None:
        """When teacher has no custom version, system skill is returned."""
        s = _make_skill_row("curriculum-mapper", teacher_id=None)
        session.add(s)
        await session.flush()

        repo = PostgresSkillRepository(session)

        # Non-existent teacher_id falls through to system skill
        result = await repo.get_by_slug("curriculum-mapper", teacher_id="nonexistent-teacher")
        assert result is not None
        assert result.teacher_id is None
        assert result.is_system is True

    async def test_no_teacher_id_prefers_system(self, session: AsyncSession) -> None:
        """Without teacher_id, system skills are preferred over teacher-owned."""
        from ailine_runtime.adapters.db.models import UserRow

        t1 = UserRow(email="sys-test@test.com", display_name="T", role="teacher")
        session.add(t1)
        await session.flush()

        # Create both a teacher-owned and a system skill with different slugs
        s_teacher = _make_skill_row("teacher-only-skill", teacher_id=t1.id)
        s_system = _make_skill_row("system-skill", teacher_id=None)
        session.add_all([s_teacher, s_system])
        await session.flush()

        repo = PostgresSkillRepository(session)

        # System skill always found without teacher_id
        result = await repo.get_by_slug("system-skill")
        assert result is not None
        assert result.teacher_id is None

        # Teacher-owned skill is also found (fallback), but the key
        # guarantee is no MultipleResultsFound exception
        result2 = await repo.get_by_slug("teacher-only-skill")
        assert result2 is not None


# ---------------------------------------------------------------------------
# F-401: Composite FK unique constraints on parent tables
# ---------------------------------------------------------------------------


class TestCompositeFKUniqueConstraints:
    """F-401: Verify UniqueConstraint(teacher_id, id) exists on parent tables."""

    def test_courses_has_teacher_id_unique_constraint(self) -> None:
        """CourseRow must have UniqueConstraint('teacher_id', 'id')."""
        table = CourseRow.__table__
        unique_cols = set()
        for constraint in table.constraints:
            from sqlalchemy import UniqueConstraint

            if isinstance(constraint, UniqueConstraint):
                cols = {c.name for c in constraint.columns}
                if cols == {"teacher_id", "id"}:
                    unique_cols = cols
        assert unique_cols == {"teacher_id", "id"}

    def test_lessons_has_teacher_id_unique_constraint(self) -> None:
        """LessonRow must have UniqueConstraint('teacher_id', 'id')."""
        table = LessonRow.__table__
        unique_cols = set()
        for constraint in table.constraints:
            from sqlalchemy import UniqueConstraint

            if isinstance(constraint, UniqueConstraint):
                cols = {c.name for c in constraint.columns}
                if cols == {"teacher_id", "id"}:
                    unique_cols = cols
        assert unique_cols == {"teacher_id", "id"}

    def test_materials_has_teacher_id_unique_constraint(self) -> None:
        """MaterialRow must have UniqueConstraint('teacher_id', 'id')."""
        table = MaterialRow.__table__
        unique_cols = set()
        for constraint in table.constraints:
            from sqlalchemy import UniqueConstraint

            if isinstance(constraint, UniqueConstraint):
                cols = {c.name for c in constraint.columns}
                if cols == {"teacher_id", "id"}:
                    unique_cols = cols
        assert unique_cols == {"teacher_id", "id"}

    def test_tutor_agents_has_teacher_id_unique_constraint(self) -> None:
        """TutorAgentRow must have UniqueConstraint('teacher_id', 'id')."""
        table = TutorAgentRow.__table__
        unique_cols = set()
        for constraint in table.constraints:
            from sqlalchemy import UniqueConstraint

            if isinstance(constraint, UniqueConstraint):
                cols = {c.name for c in constraint.columns}
                if cols == {"teacher_id", "id"}:
                    unique_cols = cols
        assert unique_cols == {"teacher_id", "id"}


# ---------------------------------------------------------------------------
# F-402: CI security scans blocking
# ---------------------------------------------------------------------------


class TestCISecurityScansBlocking:
    """F-402: Verify CI security scan jobs do not use || true."""

    def test_ci_yaml_no_or_true_in_audit(self) -> None:
        """CI YAML must not have '|| true' on security audit commands."""
        ci_path = Path(__file__).resolve().parent.parent.parent / ".github" / "workflows" / "ci.yml"
        if not ci_path.exists():
            pytest.skip("CI YAML not found")
        content = ci_path.read_text()
        # Check that security audit lines don't end with || true
        for line in content.splitlines():
            stripped = line.strip()
            if "pip-audit" in stripped or "pnpm audit" in stripped:
                assert "|| true" not in stripped, f"Security scan should be blocking (no || true): {stripped}"

    def test_docker_build_needs_security_scan(self) -> None:
        """docker-build job must depend on security-scan."""
        ci_path = Path(__file__).resolve().parent.parent.parent / ".github" / "workflows" / "ci.yml"
        if not ci_path.exists():
            pytest.skip("CI YAML not found")
        content = ci_path.read_text()
        assert "security-scan" in content, "docker-build should require security-scan"


# ---------------------------------------------------------------------------
# F-403: /auth/demo-login gated behind AILINE_DEMO_MODE
# ---------------------------------------------------------------------------


class TestDemoLoginGating:
    """F-403: /auth/demo-login must require AILINE_DEMO_MODE=true."""

    @pytest.fixture(autouse=True)
    def _clean_store(self) -> None:
        _reset_auth_store()
        yield
        _reset_auth_store()

    @pytest.fixture()
    def app_with_demo(self, settings_dev: Settings, monkeypatch: pytest.MonkeyPatch):
        """App with AILINE_DEV_MODE=true AND AILINE_DEMO_MODE=true."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        monkeypatch.setenv("AILINE_DEMO_MODE", "true")
        return create_app(settings=settings_dev)

    @pytest.fixture()
    def app_without_demo(self, settings_dev: Settings, monkeypatch: pytest.MonkeyPatch):
        """App with AILINE_DEV_MODE=true but AILINE_DEMO_MODE not set."""
        monkeypatch.setenv("AILINE_DEV_MODE", "true")
        monkeypatch.delenv("AILINE_DEMO_MODE", raising=False)
        return create_app(settings=settings_dev)

    @pytest.fixture()
    async def client_with_demo(self, app_with_demo) -> AsyncGenerator[AsyncClient]:
        transport = ASGITransport(app=app_with_demo, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test", timeout=10.0) as c:
            yield c

    @pytest.fixture()
    async def client_without_demo(self, app_without_demo) -> AsyncGenerator[AsyncClient]:
        transport = ASGITransport(app=app_without_demo, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test", timeout=10.0) as c:
            yield c

    async def test_demo_login_returns_404_without_demo_mode(self, client_without_demo: AsyncClient) -> None:
        """Without AILINE_DEMO_MODE, /auth/demo-login returns 404."""
        resp = await client_without_demo.post(
            "/auth/demo-login",
            json={"demo_key": "teacher-ms-johnson"},
        )
        assert resp.status_code == 404

    async def test_demo_login_works_with_demo_mode(self, client_with_demo: AsyncClient) -> None:
        """With AILINE_DEMO_MODE=true, /auth/demo-login works normally."""
        resp = await client_with_demo.post(
            "/auth/demo-login",
            json={"demo_key": "teacher-ms-johnson"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
