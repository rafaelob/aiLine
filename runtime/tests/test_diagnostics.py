"""Tests for the health diagnostics split (F-232).

Public ``/health/diagnostics`` — no auth, safe subset.
Private ``/internal/diagnostics`` — auth required, full operational data.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import Settings


@pytest.fixture(autouse=True)
def _force_inmemory_event_bus(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AILINE_EVENT_BUS_PROVIDER", "inmemory")
    monkeypatch.setenv("AILINE_DEV_MODE", "true")


AUTH_HEADERS = {"X-Teacher-ID": "test-diag-teacher"}


@pytest.fixture()
def app(settings: Settings):
    return create_app(settings=settings)


@pytest.fixture()
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# GET /health/diagnostics (public — no auth required)
# ---------------------------------------------------------------------------


class TestPublicDiagnostics:
    async def test_returns_200_without_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics")
        assert resp.status_code == 200

    async def test_has_status(self, client: AsyncClient) -> None:
        body = (await client.get("/health/diagnostics")).json()
        assert body["status"] in ("healthy", "degraded")

    async def test_has_dependencies_without_latency(self, client: AsyncClient) -> None:
        body = (await client.get("/health/diagnostics")).json()
        deps = body["dependencies"]
        assert "db" in deps and "redis" in deps
        assert "status" in deps["db"]
        assert "latency_ms" not in deps["db"]
        assert "latency_ms" not in deps["redis"]

    async def test_has_skills_count(self, client: AsyncClient) -> None:
        body = (await client.get("/health/diagnostics")).json()
        skills = body["skills"]
        assert "count" in skills
        assert isinstance(skills["count"], int)
        # Public should NOT expose skill names
        assert "names" not in skills

    async def test_has_uptime(self, client: AsyncClient) -> None:
        body = (await client.get("/health/diagnostics")).json()
        assert isinstance(body["uptime_seconds"], int | float)
        assert body["uptime_seconds"] >= 0

    async def test_has_environment(self, client: AsyncClient) -> None:
        body = (await client.get("/health/diagnostics")).json()
        assert body["environment"] == "development"

    async def test_has_version(self, client: AsyncClient) -> None:
        body = (await client.get("/health/diagnostics")).json()
        assert body["version"] == "0.1.0"

    async def test_no_sensitive_fields(self, client: AsyncClient) -> None:
        """Public diagnostics must NOT contain LLM config, API keys, or memory."""
        body = (await client.get("/health/diagnostics")).json()
        assert "llm" not in body
        assert "api_keys" not in body
        assert "memory" not in body

    async def test_healthy_with_skip_deps(self, client: AsyncClient) -> None:
        body = (await client.get("/health/diagnostics")).json()
        assert body["status"] == "healthy"

    async def test_content_type_json(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics")
        assert "application/json" in resp.headers["content-type"]


# ---------------------------------------------------------------------------
# GET /internal/diagnostics (authenticated — full operational data)
# ---------------------------------------------------------------------------


class TestInternalDiagnostics:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/internal/diagnostics")
        assert resp.status_code in (401, 403)

    async def test_returns_200_with_auth(self, client: AsyncClient) -> None:
        resp = await client.get("/internal/diagnostics", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    async def test_has_dependencies_with_latency(self, client: AsyncClient) -> None:
        body = (await client.get("/internal/diagnostics", headers=AUTH_HEADERS)).json()
        deps = body["dependencies"]
        assert "latency_ms" in deps["db"]
        assert "latency_ms" in deps["redis"]

    async def test_has_llm_config(self, client: AsyncClient) -> None:
        body = (await client.get("/internal/diagnostics", headers=AUTH_HEADERS)).json()
        llm = body["llm"]
        assert "provider" in llm
        assert "model" in llm
        assert "planner_model" in llm

    async def test_api_keys_are_boolean(self, client: AsyncClient) -> None:
        body = (await client.get("/internal/diagnostics", headers=AUTH_HEADERS)).json()
        for provider, present in body["api_keys"].items():
            assert isinstance(present, bool), f"{provider} should be bool"

    async def test_never_exposes_secrets(self, client: AsyncClient) -> None:
        resp = await client.get("/internal/diagnostics", headers=AUTH_HEADERS)
        assert "fake-key-for-tests" not in resp.text

    async def test_has_skills_with_names(self, client: AsyncClient) -> None:
        body = (await client.get("/internal/diagnostics", headers=AUTH_HEADERS)).json()
        skills = body["skills"]
        assert "names" in skills
        assert "count" in skills

    async def test_has_memory(self, client: AsyncClient) -> None:
        body = (await client.get("/internal/diagnostics", headers=AUTH_HEADERS)).json()
        mem = body["memory"]
        assert "pid" in mem
        assert "rss_mb" in mem

    async def test_has_uptime(self, client: AsyncClient) -> None:
        body = (await client.get("/internal/diagnostics", headers=AUTH_HEADERS)).json()
        assert isinstance(body["uptime_seconds"], int | float)

    async def test_has_overall_status(self, client: AsyncClient) -> None:
        body = (await client.get("/internal/diagnostics", headers=AUTH_HEADERS)).json()
        assert body["status"] in ("healthy", "degraded")
