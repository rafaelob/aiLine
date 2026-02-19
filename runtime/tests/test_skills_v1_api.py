"""Tests for the Skills CRUD API (F-176) -- /v1/skills endpoints.

Covers:
- GET /v1/skills: list, search, filter, pagination
- GET /v1/skills/suggest: context-based suggestions
- GET /v1/skills/{slug}: get skill detail
- POST /v1/skills: create skill (RBAC)
- PUT /v1/skills/{slug}: update skill (ownership + versioning)
- DELETE /v1/skills/{slug}: soft delete (ownership)
- POST /v1/skills/{slug}/fork: fork skill
- POST /v1/skills/{slug}/rate: rate skill (upsert)
- Auth/RBAC enforcement: unauthenticated, wrong role, tenant isolation
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.adapters.db.fake_skill_repository import FakeSkillRepository
from ailine_runtime.api.app import create_app
from ailine_runtime.api.routers.skills_v1 import set_skill_repo
from ailine_runtime.domain.entities.skill import Skill
from ailine_runtime.shared.config import (
    DatabaseConfig,
    EmbeddingConfig,
    LLMConfig,
    RedisConfig,
    Settings,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEACHER_A_ID = "teacher-aaa-1111"
TEACHER_B_ID = "teacher-bbb-2222"
STUDENT_ID = "student-ccc-3333"


@pytest.fixture()
def settings() -> Settings:
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


@pytest.fixture()
def fake_repo() -> FakeSkillRepository:
    return FakeSkillRepository()


@pytest.fixture()
def app(settings: Settings, fake_repo: FakeSkillRepository, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    # Set JWT secret so verified JWT path is used and roles are preserved
    # (without this, unverified path coerces all roles to "teacher").
    monkeypatch.setenv("AILINE_JWT_SECRET", "dev-secret-not-for-production-use-32bytes!")
    set_skill_repo(fake_repo)
    application = create_app(settings=settings)
    yield application
    set_skill_repo(None)  # type: ignore[arg-type]


@pytest.fixture()
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport, base_url="http://test", timeout=10.0
    ) as c:
        yield c


def _auth_header(teacher_id: str) -> dict[str, str]:
    """Build auth header for dev mode (X-Teacher-ID)."""
    return {"X-Teacher-ID": teacher_id}


async def _login_and_get_token(
    client: AsyncClient,
    email: str,
    role: str = "teacher",
) -> str:
    """Login via dev mode and return the JWT token."""
    resp = await client.post(
        "/auth/login",
        json={"email": email, "role": role},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _seed_skill(
    fake_repo: FakeSkillRepository,
    slug: str,
    teacher_id: str | None = None,
    is_system: bool = False,
    description: str = "A test skill",
) -> Skill:
    """Seed a skill directly into the fake repo."""
    skill = Skill(
        slug=slug,
        description=description,
        instructions_md=f"Instructions for {slug}",
        metadata={"category": "test", "version": "1.0.0"},
        license="MIT",
        compatibility="pydantic-ai",
        allowed_tools="web-search calculator",
    )
    await fake_repo.create(skill, teacher_id=teacher_id, is_system=is_system)
    return skill


# ---------------------------------------------------------------------------
# GET /v1/skills -- List
# ---------------------------------------------------------------------------


class TestListSkills:
    """Tests for GET /v1/skills."""

    async def test_list_empty(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get(
            "/v1/skills",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0
        assert body["skills"] == []

    async def test_list_returns_seeded_skills(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "skill-alpha", teacher_id=TEACHER_A_ID)
        await _seed_skill(fake_repo, "skill-beta", teacher_id=TEACHER_A_ID)

        resp = await client.get(
            "/v1/skills",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 2
        slugs = [s["slug"] for s in body["skills"]]
        assert "skill-alpha" in slugs
        assert "skill-beta" in slugs

    async def test_list_excludes_inactive(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "active-skill", teacher_id=TEACHER_A_ID)
        await _seed_skill(fake_repo, "deleted-skill", teacher_id=TEACHER_A_ID)
        await fake_repo.soft_delete("deleted-skill")

        resp = await client.get(
            "/v1/skills",
            headers=_auth_header(TEACHER_A_ID),
        )
        body = resp.json()
        assert body["count"] == 1
        assert body["skills"][0]["slug"] == "active-skill"

    async def test_list_system_only_filter(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "user-skill", teacher_id=TEACHER_A_ID)
        await _seed_skill(fake_repo, "system-skill", is_system=True)

        resp = await client.get(
            "/v1/skills?system_only=true",
            headers=_auth_header(TEACHER_A_ID),
        )
        body = resp.json()
        assert body["count"] == 1
        assert body["skills"][0]["slug"] == "system-skill"

    async def test_list_filter_by_teacher(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "a-skill", teacher_id=TEACHER_A_ID)
        await _seed_skill(fake_repo, "b-skill", teacher_id=TEACHER_B_ID)

        resp = await client.get(
            f"/v1/skills?teacher_id={TEACHER_A_ID}",
            headers=_auth_header(TEACHER_A_ID),
        )
        body = resp.json()
        assert body["count"] == 1
        assert body["skills"][0]["slug"] == "a-skill"

    async def test_list_pagination(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        for i in range(5):
            await _seed_skill(fake_repo, f"skill-{i:02d}", teacher_id=TEACHER_A_ID)

        resp = await client.get(
            "/v1/skills?limit=2&offset=0",
            headers=_auth_header(TEACHER_A_ID),
        )
        body = resp.json()
        assert body["count"] == 5  # total count, not page size
        assert len(body["skills"]) == 2

        resp2 = await client.get(
            "/v1/skills?limit=2&offset=2",
            headers=_auth_header(TEACHER_A_ID),
        )
        body2 = resp2.json()
        assert body2["count"] == 5
        assert len(body2["skills"]) == 2

        resp3 = await client.get(
            "/v1/skills?limit=2&offset=4",
            headers=_auth_header(TEACHER_A_ID),
        )
        body3 = resp3.json()
        assert body3["count"] == 5
        assert len(body3["skills"]) == 1  # only 1 remaining

    async def test_list_summaries_exclude_instructions(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "no-instructions-in-list", teacher_id=TEACHER_A_ID)

        resp = await client.get(
            "/v1/skills",
            headers=_auth_header(TEACHER_A_ID),
        )
        skill_data = resp.json()["skills"][0]
        assert "instructions_md" not in skill_data


# ---------------------------------------------------------------------------
# GET /v1/skills -- Text search
# ---------------------------------------------------------------------------


class TestSearchSkills:
    """Tests for GET /v1/skills?q=..."""

    async def test_search_by_slug(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "quiz-generator", teacher_id=TEACHER_A_ID)
        await _seed_skill(fake_repo, "lesson-planner", teacher_id=TEACHER_A_ID)

        resp = await client.get(
            "/v1/skills?q=quiz",
            headers=_auth_header(TEACHER_A_ID),
        )
        body = resp.json()
        assert body["count"] == 1
        assert body["skills"][0]["slug"] == "quiz-generator"

    async def test_search_by_description(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(
            fake_repo,
            "my-skill",
            teacher_id=TEACHER_A_ID,
            description="Generates math worksheets",
        )

        resp = await client.get(
            "/v1/skills?q=math",
            headers=_auth_header(TEACHER_A_ID),
        )
        body = resp.json()
        assert body["count"] == 1

    async def test_search_no_results(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "some-skill", teacher_id=TEACHER_A_ID)

        resp = await client.get(
            "/v1/skills?q=nonexistent",
            headers=_auth_header(TEACHER_A_ID),
        )
        body = resp.json()
        assert body["count"] == 0


# ---------------------------------------------------------------------------
# GET /v1/skills/suggest
# ---------------------------------------------------------------------------


class TestSuggestSkills:
    """Tests for GET /v1/skills/suggest."""

    async def test_suggest_returns_matching_skills(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(
            fake_repo,
            "math-tutor",
            teacher_id=TEACHER_A_ID,
            description="Tutoring for math and algebra",
        )
        await _seed_skill(
            fake_repo,
            "reading-coach",
            teacher_id=TEACHER_A_ID,
            description="Reading comprehension support",
        )

        # FakeSkillRepository uses substring matching, so use a term
        # that appears in the description
        resp = await client.get(
            "/v1/skills/suggest?context=math",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] >= 1
        slugs = [s["slug"] for s in body["skills"]]
        assert "math-tutor" in slugs

    async def test_suggest_requires_context(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get(
            "/v1/skills/suggest",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 422

    async def test_suggest_respects_limit(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        for i in range(10):
            await _seed_skill(
                fake_repo,
                f"skill-{i}",
                teacher_id=TEACHER_A_ID,
                description=f"skill about topic {i}",
            )

        resp = await client.get(
            "/v1/skills/suggest?context=skill&limit=3",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.json()["count"] <= 3


# ---------------------------------------------------------------------------
# GET /v1/skills/{slug}
# ---------------------------------------------------------------------------


class TestGetSkill:
    """Tests for GET /v1/skills/{slug}."""

    async def test_get_existing_skill(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "detail-skill", teacher_id=TEACHER_A_ID)

        resp = await client.get(
            "/v1/skills/detail-skill",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["slug"] == "detail-skill"
        assert "instructions_md" in body
        assert "metadata" in body
        assert body["instructions_md"] == "Instructions for detail-skill"

    async def test_get_nonexistent_returns_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.get(
            "/v1/skills/does-not-exist",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 404

    async def test_get_deleted_skill_returns_404(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "deleted-one", teacher_id=TEACHER_A_ID)
        await fake_repo.soft_delete("deleted-one")

        resp = await client.get(
            "/v1/skills/deleted-one",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /v1/skills -- Create
# ---------------------------------------------------------------------------


class TestCreateSkill:
    """Tests for POST /v1/skills."""

    async def test_create_skill_success(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/v1/skills",
            json={
                "slug": "new-skill",
                "title": "New Skill",
                "description": "A brand new skill",
                "instructions_md": "# New Skill\nDo this.",
                "license": "MIT",
                "metadata_json": {"category": "education"},
            },
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["slug"] == "new-skill"
        assert body["description"] == "A brand new skill"
        assert body["instructions_md"] == "# New Skill\nDo this."
        assert body["teacher_id"] == TEACHER_A_ID
        assert body["version"] == 1
        assert body["is_active"] is True

    async def test_create_duplicate_slug_returns_409(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "existing-slug", teacher_id=TEACHER_A_ID)

        resp = await client.post(
            "/v1/skills",
            json={"slug": "existing-slug", "description": "Duplicate"},
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    async def test_create_requires_slug(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/v1/skills",
            json={"description": "No slug"},
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 422

    async def test_create_sets_description_from_title_if_empty(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/v1/skills",
            json={"slug": "title-as-desc", "title": "My Title"},
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 201
        assert resp.json()["description"] == "My Title"

    async def test_create_with_all_fields(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/v1/skills",
            json={
                "slug": "full-skill",
                "title": "Full Skill",
                "description": "Complete skill",
                "instructions_md": "Do everything",
                "metadata_json": {"version": "2.0.0"},
                "license": "Apache-2.0",
                "compatibility": "pydantic-ai langchain",
                "allowed_tools": "web-search calculator",
            },
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["license"] == "Apache-2.0"
        assert body["compatibility"] == "pydantic-ai langchain"
        assert body["allowed_tools"] == "web-search calculator"


# ---------------------------------------------------------------------------
# PUT /v1/skills/{slug} -- Update
# ---------------------------------------------------------------------------


class TestUpdateSkill:
    """Tests for PUT /v1/skills/{slug}."""

    async def test_update_own_skill(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "updatable", teacher_id=TEACHER_A_ID)

        resp = await client.put(
            "/v1/skills/updatable",
            json={
                "description": "Updated description",
                "instructions_md": "Updated instructions",
                "change_summary": "Updated for testing",
            },
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["description"] == "Updated description"
        assert body["instructions_md"] == "Updated instructions"
        assert body["version"] == 2

    async def test_update_other_teacher_skill_returns_403(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "not-mine", teacher_id=TEACHER_A_ID)

        resp = await client.put(
            "/v1/skills/not-mine",
            json={"description": "Hijacked"},
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp.status_code == 403

    async def test_update_nonexistent_returns_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.put(
            "/v1/skills/ghost-skill",
            json={"description": "???"},
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 404

    async def test_update_partial_fields(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "partial-update", teacher_id=TEACHER_A_ID)

        resp = await client.put(
            "/v1/skills/partial-update",
            json={"description": "Only description changed"},
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["description"] == "Only description changed"
        # instructions_md should remain unchanged
        assert body["instructions_md"] == "Instructions for partial-update"

    async def test_update_increments_version(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "versioned", teacher_id=TEACHER_A_ID)

        await client.put(
            "/v1/skills/versioned",
            json={"description": "v2"},
            headers=_auth_header(TEACHER_A_ID),
        )
        resp = await client.put(
            "/v1/skills/versioned",
            json={"description": "v3"},
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.json()["version"] == 3


# ---------------------------------------------------------------------------
# DELETE /v1/skills/{slug}
# ---------------------------------------------------------------------------


class TestDeleteSkill:
    """Tests for DELETE /v1/skills/{slug}."""

    async def test_delete_own_skill(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "deletable", teacher_id=TEACHER_A_ID)

        resp = await client.delete(
            "/v1/skills/deletable",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 204

        # Verify it's soft-deleted
        get_resp = await client.get(
            "/v1/skills/deletable",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert get_resp.status_code == 404

    async def test_delete_other_teacher_skill_returns_403(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "not-deletable", teacher_id=TEACHER_A_ID)

        resp = await client.delete(
            "/v1/skills/not-deletable",
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp.status_code == 403

    async def test_delete_nonexistent_returns_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.delete(
            "/v1/skills/phantom",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 404

    async def test_delete_is_idempotent_for_already_deleted(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "double-delete", teacher_id=TEACHER_A_ID)
        await client.delete(
            "/v1/skills/double-delete",
            headers=_auth_header(TEACHER_A_ID),
        )
        # Second delete should return 404 (already inactive)
        resp = await client.delete(
            "/v1/skills/double-delete",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /v1/skills/{slug}/fork
# ---------------------------------------------------------------------------


class TestForkSkill:
    """Tests for POST /v1/skills/{slug}/fork."""

    async def test_fork_creates_new_skill(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "forkable", teacher_id=TEACHER_A_ID)

        resp = await client.post(
            "/v1/skills/forkable/fork",
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["slug"] == "forkable-fork"
        assert body["teacher_id"] == TEACHER_B_ID
        assert body["forked_from_id"] is not None

    async def test_fork_nonexistent_returns_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/v1/skills/no-such-skill/fork",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 404

    async def test_fork_preserves_content(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "content-fork", teacher_id=TEACHER_A_ID)

        resp = await client.post(
            "/v1/skills/content-fork/fork",
            headers=_auth_header(TEACHER_B_ID),
        )
        body = resp.json()
        assert body["description"] == "A test skill"
        assert "Instructions for content-fork" in body["instructions_md"]
        assert body["version"] == 1


# ---------------------------------------------------------------------------
# POST /v1/skills/{slug}/rate
# ---------------------------------------------------------------------------


class TestRateSkill:
    """Tests for POST /v1/skills/{slug}/rate."""

    async def test_rate_skill_success(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "rateable", teacher_id=TEACHER_A_ID)

        resp = await client.post(
            "/v1/skills/rateable/rate",
            json={"score": 4, "comment": "Great skill!"},
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["slug"] == "rateable"
        assert body["score"] == 4
        assert body["avg_rating"] == 4.0
        assert body["rating_count"] == 1

    async def test_rate_upsert(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "upsert-rate", teacher_id=TEACHER_A_ID)

        # First rating
        await client.post(
            "/v1/skills/upsert-rate/rate",
            json={"score": 3},
            headers=_auth_header(TEACHER_B_ID),
        )
        # Update rating
        resp = await client.post(
            "/v1/skills/upsert-rate/rate",
            json={"score": 5},
            headers=_auth_header(TEACHER_B_ID),
        )
        body = resp.json()
        assert body["avg_rating"] == 5.0
        assert body["rating_count"] == 1  # Same user, upserted

    async def test_rate_nonexistent_returns_404(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/v1/skills/no-skill/rate",
            json={"score": 3},
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 404

    async def test_rate_invalid_score_returns_422(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "bad-score", teacher_id=TEACHER_A_ID)

        resp = await client.post(
            "/v1/skills/bad-score/rate",
            json={"score": 0},
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp.status_code == 422

        resp2 = await client.post(
            "/v1/skills/bad-score/rate",
            json={"score": 6},
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp2.status_code == 422

    async def test_rate_multiple_users(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "multi-rate", teacher_id=TEACHER_A_ID)

        await client.post(
            "/v1/skills/multi-rate/rate",
            json={"score": 2},
            headers=_auth_header(TEACHER_A_ID),
        )
        resp = await client.post(
            "/v1/skills/multi-rate/rate",
            json={"score": 4},
            headers=_auth_header(TEACHER_B_ID),
        )
        body = resp.json()
        assert body["rating_count"] == 2
        assert body["avg_rating"] == 3.0  # (2 + 4) / 2


# ---------------------------------------------------------------------------
# Auth/RBAC enforcement
# ---------------------------------------------------------------------------


class TestAuthEnforcement:
    """Tests for authentication and RBAC on skills endpoints."""

    async def test_list_without_auth_returns_401(
        self, settings: Settings, fake_repo: FakeSkillRepository,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Without any auth headers, requests should be rejected."""
        monkeypatch.setenv("AILINE_DEV_MODE", "false")
        set_skill_repo(fake_repo)
        non_dev_app = create_app(settings=settings)
        transport = ASGITransport(app=non_dev_app, raise_app_exceptions=False)
        async with AsyncClient(
            transport=transport, base_url="http://test", timeout=10.0
        ) as non_dev_client:
            resp = await non_dev_client.get("/v1/skills")
            assert resp.status_code == 401

    async def test_get_without_auth_returns_401(
        self, settings: Settings, fake_repo: FakeSkillRepository,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("AILINE_DEV_MODE", "false")
        set_skill_repo(fake_repo)
        non_dev_app = create_app(settings=settings)
        transport = ASGITransport(app=non_dev_app, raise_app_exceptions=False)
        async with AsyncClient(
            transport=transport, base_url="http://test", timeout=10.0
        ) as non_dev_client:
            resp = await non_dev_client.get("/v1/skills/some-slug")
            assert resp.status_code == 401

    async def test_create_with_student_role_returns_error(
        self, client: AsyncClient
    ) -> None:
        """Students should not be able to create skills."""
        token = await _login_and_get_token(client, "student@skills-test.com", role="student")
        resp = await client.post(
            "/v1/skills",
            json={"slug": "student-skill", "description": "Not allowed"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Student role is not in require_teacher_or_admin: should get 400 or 403
        assert resp.status_code in (400, 403)

    async def test_student_can_list_skills(
        self, client: AsyncClient
    ) -> None:
        """Students can read skills (list endpoint)."""
        token = await _login_and_get_token(client, "student-reader@skills-test.com", role="student")
        resp = await client.get(
            "/v1/skills",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_student_can_rate_skills(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        """Students can rate skills (any authenticated user)."""
        await _seed_skill(fake_repo, "student-rateable", teacher_id=TEACHER_A_ID)
        token = await _login_and_get_token(client, "student-rater@skills-test.com", role="student")
        resp = await client.post(
            "/v1/skills/student-rateable/rate",
            json={"score": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------


class TestTenantIsolation:
    """Tests for tenant isolation -- can't update/delete other teachers' skills."""

    async def test_teacher_b_cannot_update_teacher_a_skill(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "a-only", teacher_id=TEACHER_A_ID)

        resp = await client.put(
            "/v1/skills/a-only",
            json={"description": "Hijacked by B"},
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp.status_code == 403

    async def test_teacher_b_cannot_delete_teacher_a_skill(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "a-protected", teacher_id=TEACHER_A_ID)

        resp = await client.delete(
            "/v1/skills/a-protected",
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp.status_code == 403

    async def test_any_teacher_can_read_other_teacher_skill(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        """Read access is not restricted by ownership."""
        await _seed_skill(fake_repo, "a-public", teacher_id=TEACHER_A_ID)

        resp = await client.get(
            "/v1/skills/a-public",
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp.status_code == 200

    async def test_any_teacher_can_fork_other_teacher_skill(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "a-forkable", teacher_id=TEACHER_A_ID)

        resp = await client.post(
            "/v1/skills/a-forkable/fork",
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp.status_code == 201
        assert resp.json()["teacher_id"] == TEACHER_B_ID


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge case tests."""

    async def test_create_skill_with_empty_metadata(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/v1/skills",
            json={"slug": "empty-meta", "metadata_json": {}},
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 201

    async def test_skill_detail_includes_metadata_dict(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "meta-skill", teacher_id=TEACHER_A_ID)

        resp = await client.get(
            "/v1/skills/meta-skill",
            headers=_auth_header(TEACHER_A_ID),
        )
        body = resp.json()
        assert isinstance(body["metadata"], dict)
        assert body["metadata"]["category"] == "test"

    async def test_rate_without_comment(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "no-comment-rate", teacher_id=TEACHER_A_ID)

        resp = await client.post(
            "/v1/skills/no-comment-rate/rate",
            json={"score": 3},
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp.status_code == 200

    async def test_list_with_limit_1(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "limit-a", teacher_id=TEACHER_A_ID)
        await _seed_skill(fake_repo, "limit-b", teacher_id=TEACHER_A_ID)

        resp = await client.get(
            "/v1/skills?limit=1",
            headers=_auth_header(TEACHER_A_ID),
        )
        body = resp.json()
        assert body["count"] == 2  # total, not page size
        assert len(body["skills"]) == 1

    async def test_suggest_with_no_matching_skills(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "alpha-skill", teacher_id=TEACHER_A_ID)

        resp = await client.get(
            "/v1/skills/suggest?context=zzz-nonexistent-term",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    async def test_create_and_get_roundtrip(
        self, client: AsyncClient
    ) -> None:
        """Create a skill and immediately retrieve it."""
        await client.post(
            "/v1/skills",
            json={
                "slug": "roundtrip-skill",
                "description": "Roundtrip test",
                "instructions_md": "# Instructions\nStep 1...",
                "license": "MIT",
            },
            headers=_auth_header(TEACHER_A_ID),
        )

        resp = await client.get(
            "/v1/skills/roundtrip-skill",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["slug"] == "roundtrip-skill"
        assert body["description"] == "Roundtrip test"
        assert body["license"] == "MIT"

    async def test_create_update_delete_lifecycle(
        self, client: AsyncClient
    ) -> None:
        """Full CRUD lifecycle."""
        # Create
        create_resp = await client.post(
            "/v1/skills",
            json={"slug": "lifecycle", "description": "v1"},
            headers=_auth_header(TEACHER_A_ID),
        )
        assert create_resp.status_code == 201
        assert create_resp.json()["version"] == 1

        # Update
        update_resp = await client.put(
            "/v1/skills/lifecycle",
            json={"description": "v2", "change_summary": "Updated desc"},
            headers=_auth_header(TEACHER_A_ID),
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["version"] == 2
        assert update_resp.json()["description"] == "v2"

        # Delete
        delete_resp = await client.delete(
            "/v1/skills/lifecycle",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert delete_resp.status_code == 204

        # Verify deleted
        get_resp = await client.get(
            "/v1/skills/lifecycle",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert get_resp.status_code == 404


# ---------------------------------------------------------------------------
# Pagination count fix (Sprint 27)
# ---------------------------------------------------------------------------


class TestPaginationCount:
    """count must reflect total matching skills, not paginated subset."""

    async def test_count_returns_total_not_page_size(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        for i in range(5):
            await _seed_skill(fake_repo, f"page-skill-{i}", is_system=True)

        resp = await client.get(
            "/v1/skills?limit=2&offset=0&system_only=true",
            headers=_auth_header(TEACHER_A_ID),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 5  # total, not 2
        assert len(body["skills"]) == 2

    async def test_offset_pages_correctly(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        for i in range(5):
            await _seed_skill(fake_repo, f"off-skill-{i}", is_system=True)

        resp = await client.get(
            "/v1/skills?limit=2&offset=3&system_only=true",
            headers=_auth_header(TEACHER_A_ID),
        )
        body = resp.json()
        assert body["count"] == 5
        assert len(body["skills"]) == 2  # skills 3 and 4


# ---------------------------------------------------------------------------
# Fork slug collision (Sprint 27)
# ---------------------------------------------------------------------------


class TestForkSlugCollision:
    """Fork uses counter suffix when slug collides."""

    async def test_double_fork_gets_counter_suffix(
        self, client: AsyncClient, fake_repo: FakeSkillRepository
    ) -> None:
        await _seed_skill(fake_repo, "double-fork", teacher_id=TEACHER_A_ID)

        # First fork
        resp1 = await client.post(
            "/v1/skills/double-fork/fork",
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp1.status_code == 201
        assert resp1.json()["slug"] == "double-fork-fork"

        # Second fork (collision) -- should get counter suffix
        resp2 = await client.post(
            "/v1/skills/double-fork/fork",
            headers=_auth_header(TEACHER_B_ID),
        )
        assert resp2.status_code == 201
        assert resp2.json()["slug"] == "double-fork-fork-2"
