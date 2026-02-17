"""Tests for the enhanced /health/diagnostics endpoint.

Covers:
- Diagnostics returns expected structure
- Dependency status with latency
- LLM config info (no secrets)
- API key presence (boolean, never actual keys)
- Skills loaded status
- Memory usage
- Uptime tracking
- Overall status determination
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
# GET /health/diagnostics
# ---------------------------------------------------------------------------


class TestHealthDiagnostics:
    async def test_diagnostics_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        assert resp.status_code == 200

    async def test_diagnostics_has_dependencies(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        body = resp.json()
        assert "dependencies" in body
        deps = body["dependencies"]
        assert "db" in deps
        assert "redis" in deps
        # Each dep has status and latency
        assert "status" in deps["db"]
        assert "latency_ms" in deps["db"]
        assert "status" in deps["redis"]
        assert "latency_ms" in deps["redis"]

    async def test_diagnostics_has_llm_config(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        body = resp.json()
        assert "llm" in body
        llm = body["llm"]
        assert "provider" in llm
        assert "model" in llm
        assert "planner_model" in llm
        assert "executor_model" in llm
        assert "qg_model" in llm
        assert "tutor_model" in llm

    async def test_diagnostics_api_keys_are_boolean(self, client: AsyncClient) -> None:
        """API key presence must be boolean, never the actual key."""
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        body = resp.json()
        assert "api_keys" in body
        keys = body["api_keys"]
        for provider, present in keys.items():
            assert isinstance(
                present, bool
            ), f"{provider} should be bool, got {type(present)}"

    async def test_diagnostics_never_exposes_secrets(self, client: AsyncClient) -> None:
        """Ensure no actual API key values leak into diagnostics."""
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        text = resp.text
        # The test settings use "fake-key-for-tests" — this must NOT appear
        assert "fake-key-for-tests" not in text

    async def test_diagnostics_has_skills(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        body = resp.json()
        assert "skills" in body
        skills = body["skills"]
        assert "loaded" in skills
        assert "count" in skills
        assert isinstance(skills["count"], int)

    async def test_diagnostics_has_memory(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        body = resp.json()
        assert "memory" in body
        mem = body["memory"]
        assert "pid" in mem
        assert "rss_mb" in mem

    async def test_diagnostics_has_uptime(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        body = resp.json()
        assert "uptime_seconds" in body
        assert isinstance(body["uptime_seconds"], int | float)
        assert body["uptime_seconds"] >= 0

    async def test_diagnostics_has_environment(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        body = resp.json()
        assert "environment" in body
        assert body["environment"] == "development"

    async def test_diagnostics_has_version(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        body = resp.json()
        assert "version" in body
        assert body["version"] == "0.1.0"

    async def test_diagnostics_has_overall_status(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        body = resp.json()
        assert "status" in body
        assert body["status"] in ("healthy", "degraded")

    async def test_diagnostics_healthy_with_skip_deps(
        self, client: AsyncClient
    ) -> None:
        """With test settings (SQLite dev, in-memory bus), status is healthy."""
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        body = resp.json()
        # Both deps should be "skip" which counts as OK
        assert body["status"] == "healthy"

    async def test_diagnostics_content_type(self, client: AsyncClient) -> None:
        resp = await client.get("/health/diagnostics", headers=AUTH_HEADERS)
        assert "application/json" in resp.headers["content-type"]

    async def test_diagnostics_requires_auth(self, client: AsyncClient) -> None:
        """Diagnostics endpoint requires authentication (SEC-03)."""
        resp = await client.get("/health/diagnostics")
        # Should fail without auth header
        assert resp.status_code in (401, 403)
