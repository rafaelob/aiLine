"""Tests for the /health endpoint and application factory."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import Settings


@pytest.fixture()
def app(settings: Settings):
    """Create a FastAPI app with test settings."""
    return create_app(settings=settings)


@pytest.fixture()
async def client(app) -> AsyncClient:
    """Async HTTP client bound to the test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


async def test_health_returns_ok(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"status": "ok"}


async def test_health_content_type_is_json(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert "application/json" in resp.headers["content-type"]


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def test_create_app_returns_fastapi(settings: Settings) -> None:
    app = create_app(settings=settings)
    assert app.title == "AiLine Runtime API"
    assert app.version == "0.1.0"


def test_create_app_registers_routers(settings: Settings) -> None:
    app = create_app(settings=settings)
    route_paths = [r.path for r in app.routes]
    # Check that key router prefixes are registered
    assert any("/materials" in p for p in route_paths)
    assert any("/plans" in p for p in route_paths)
    assert any("/tutors" in p for p in route_paths)


def test_create_app_stores_container(settings: Settings) -> None:
    app = create_app(settings=settings)
    assert hasattr(app.state, "container")
    assert hasattr(app.state, "settings")
    assert app.state.container is not None


async def test_unknown_route_returns_404(client: AsyncClient) -> None:
    resp = await client.get("/nonexistent")
    assert resp.status_code == 404
