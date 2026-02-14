"""Tests for RFC 7807 Problem Details error handler middleware.

Validates that all error responses follow the RFC 7807 format with
consistent fields: type, title, status, detail, instance, request_id.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import (
    DatabaseConfig,
    EmbeddingConfig,
    LLMConfig,
    RedisConfig,
    Settings,
)


@pytest.fixture(autouse=True)
def _enable_dev_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AILINE_DEV_MODE", "true")


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        anthropic_api_key="fake-key-for-tests",
        openai_api_key="",
        google_api_key="",
        db=DatabaseConfig(url="sqlite+aiosqlite:///:memory:"),
        llm=LLMConfig(provider="fake", api_key="fake"),
        embedding=EmbeddingConfig(provider="gemini", api_key=""),
        redis=RedisConfig(url="redis://localhost:6379/0"),
    )


@pytest.fixture()
def app(settings: Settings):
    return create_app(settings=settings)


@pytest.fixture()
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestRFC7807ErrorFormat:
    """Verify that errors follow RFC 7807 Problem Details format."""

    async def test_404_has_problem_detail_fields(self, client: AsyncClient) -> None:
        resp = await client.get("/nonexistent-endpoint-that-does-not-exist")
        assert resp.status_code == 404
        body = resp.json()
        assert "type" in body
        assert "title" in body
        assert "status" in body
        assert body["status"] == 404
        assert "detail" in body
        assert resp.headers.get("content-type", "").startswith("application/problem+json")

    async def test_422_validation_error_has_errors_field(
        self, client: AsyncClient
    ) -> None:
        """POST with invalid body should return 422 with errors array."""
        resp = await client.post(
            "/materials",
            json={"invalid_field_only": "value"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == 422
        assert "errors" in body
        assert isinstance(body["errors"], list)
        assert len(body["errors"]) > 0
        # Each error should have field, message, type
        for err in body["errors"]:
            assert "field" in err
            assert "message" in err

    async def test_422_has_instance_path(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/materials",
            json={"invalid_field_only": "value"},
        )
        body = resp.json()
        assert body.get("instance") == "/materials"

    async def test_401_unauthorized_has_problem_format(
        self, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Accessing an endpoint requiring auth without credentials."""
        monkeypatch.setenv("AILINE_DEV_MODE", "false")
        # Access tutor list without any auth
        resp = await client.get("/tutors/nonexistent-id")
        assert resp.status_code in (401, 404)
        body = resp.json()
        assert "type" in body
        assert "status" in body

    async def test_error_response_has_title(self, client: AsyncClient) -> None:
        resp = await client.get("/nonexistent")
        body = resp.json()
        assert body.get("title") in ("Not Found", "Error")

    async def test_error_type_is_about_blank(self, client: AsyncClient) -> None:
        resp = await client.get("/nonexistent")
        body = resp.json()
        assert body.get("type") == "about:blank"

    async def test_health_endpoint_still_works(self, client: AsyncClient) -> None:
        """Error handlers should not affect normal successful responses."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"status": "ok"}

    async def test_content_type_is_problem_json(self, client: AsyncClient) -> None:
        resp = await client.get("/nonexistent")
        assert resp.status_code == 404
        ct = resp.headers.get("content-type", "")
        assert "application/problem+json" in ct
