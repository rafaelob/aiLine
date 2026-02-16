"""Tests for the Skills Discovery API (/skills endpoints).

Covers:
- GET /skills — list with filtering and search
- GET /skills/{slug} — detail with instructions preview
- GET /skills/policy/{profile} — accessibility policy resolution
- GET /skills/policies — all policies summary
- Auth enforcement on all endpoints
- Graceful degradation when registry is unavailable
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import Settings


@pytest.fixture(autouse=True)
def _force_inmemory_event_bus(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AILINE_EVENT_BUS_PROVIDER", "inmemory")


@pytest.fixture(autouse=True)
def _clear_registry_cache() -> None:
    """Clear the cached registry between tests."""
    from ailine_runtime.api.routers.skills import _get_registry_cached

    _get_registry_cached.cache_clear()


@pytest.fixture()
def app(settings: Settings):
    return create_app(settings=settings)


@pytest.fixture()
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture()
async def auth_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Client with dev-mode teacher auth header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Teacher-ID": "test-teacher-001"},
    ) as c:
        yield c


@pytest.fixture(autouse=True)
def _enable_dev_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable dev mode so X-Teacher-ID header is accepted."""
    monkeypatch.setenv("AILINE_DEV_MODE", "true")


# ---------------------------------------------------------------------------
# GET /skills — list all skills
# ---------------------------------------------------------------------------


class TestListSkills:
    async def test_list_skills_returns_skills(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/skills")
        assert resp.status_code == 200
        body = resp.json()
        assert "count" in body
        assert "categories" in body
        assert "skills" in body
        assert isinstance(body["skills"], list)

    async def test_list_skills_has_expected_fields(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/skills")
        body = resp.json()
        if body["count"] > 0:
            skill = body["skills"][0]
            assert "slug" in skill
            assert "name" in skill
            assert "description" in skill
            assert "category" in skill
            assert "has_instructions" in skill

    async def test_list_skills_search_filter(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/skills", params={"q": "accessibility"})
        assert resp.status_code == 200
        body = resp.json()
        # All results should match the search term
        for skill in body["skills"]:
            assert "accessibility" in skill["name"].lower() or "accessibility" in skill["description"].lower()

    async def test_list_skills_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/skills")
        assert resp.status_code in (401, 403)

    async def test_list_skills_cache_header(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/skills")
        assert "max-age" in resp.headers.get("cache-control", "")

    async def test_list_skills_graceful_when_registry_unavailable(
        self, auth_client: AsyncClient,
    ) -> None:
        with patch(
            "ailine_runtime.api.routers.skills._get_registry", return_value=None,
        ):
            resp = await auth_client.get("/skills")
            assert resp.status_code == 200
            body = resp.json()
            assert body["count"] == 0
            assert body["skills"] == []


# ---------------------------------------------------------------------------
# GET /skills/{slug} — skill detail
# ---------------------------------------------------------------------------


class TestGetSkillDetail:
    async def test_get_existing_skill(self, auth_client: AsyncClient) -> None:
        # First list to get a slug
        list_resp = await auth_client.get("/skills")
        skills = list_resp.json().get("skills", [])
        if not skills:
            pytest.skip("No skills loaded in test environment")

        slug = skills[0]["slug"]
        resp = await auth_client.get(f"/skills/{slug}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["slug"] == slug
        assert "instructions_preview" in body
        assert "instructions_length" in body
        assert "metadata" in body

    async def test_get_nonexistent_skill_returns_404(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/skills/nonexistent-skill-xyz")
        assert resp.status_code == 404

    async def test_get_skill_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/skills/accessibility-adaptor")
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /skills/policy/{profile} — accessibility policy
# ---------------------------------------------------------------------------


class TestSkillPolicy:
    async def test_policy_for_autism(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/skills/policy/autism")
        assert resp.status_code == 200
        body = resp.json()
        assert body["profile"] == "autism"
        assert "skills" in body
        assert "needs_human_review" in body
        assert "skill_count" in body
        assert isinstance(body["skills"], list)
        # Autism policy should include accessibility-coach as must
        slugs = [s["slug"] for s in body["skills"]]
        assert "accessibility-coach" in slugs

    async def test_policy_for_hearing_requires_human_review(
        self, auth_client: AsyncClient,
    ) -> None:
        resp = await auth_client.get("/skills/policy/hearing")
        assert resp.status_code == 200
        body = resp.json()
        assert body["profile"] == "hearing"
        # Hearing includes sign-language-interpreter which triggers review
        assert body["needs_human_review"] is True

    async def test_policy_with_max_skills_param(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/skills/policy/autism", params={"max_skills": 3})
        assert resp.status_code == 200
        body = resp.json()
        assert body["skill_count"] <= 3

    async def test_policy_for_unknown_profile_returns_404(
        self, auth_client: AsyncClient,
    ) -> None:
        resp = await auth_client.get("/skills/policy/nonexistent")
        assert resp.status_code == 404

    async def test_all_valid_profiles(self, auth_client: AsyncClient) -> None:
        profiles = ["autism", "adhd", "learning", "hearing", "visual", "speech_language", "motor"]
        for profile in profiles:
            resp = await auth_client.get(f"/skills/policy/{profile}")
            assert resp.status_code == 200, f"Failed for profile: {profile}"
            body = resp.json()
            assert body["profile"] == profile
            assert body["skill_count"] > 0

    async def test_policy_skills_have_priority_field(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/skills/policy/adhd")
        body = resp.json()
        for skill in body["skills"]:
            assert "slug" in skill
            assert "reason" in skill
            assert "priority" in skill


# ---------------------------------------------------------------------------
# GET /skills/policies — all policies summary
# ---------------------------------------------------------------------------


class TestListAllPolicies:
    async def test_list_all_policies(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/skills/policies")
        assert resp.status_code == 200
        body = resp.json()
        assert "profiles" in body
        profiles = body["profiles"]
        # Should have all 7 accessibility profiles
        expected = {"autism", "adhd", "learning", "hearing", "visual", "speech_language", "motor"}
        assert set(profiles.keys()) == expected

    async def test_policy_structure(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/skills/policies")
        body = resp.json()
        for _name, policy in body["profiles"].items():
            assert "must" in policy
            assert "should" in policy
            assert "nice" in policy
            assert "human_review_triggers" in policy
            assert "total_skills" in policy
            assert isinstance(policy["must"], list)
