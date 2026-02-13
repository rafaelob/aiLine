"""Tests for the /health, /health/ready endpoints, security headers,
request ID middleware, and application factory."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import Settings


@pytest.fixture(autouse=True)
def _force_inmemory_event_bus(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force InMemoryEventBus so Redis connectivity is not required."""
    monkeypatch.setenv("AILINE_EVENT_BUS_PROVIDER", "inmemory")


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
# Liveness probe: /health
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
# Readiness probe: /health/ready
# ---------------------------------------------------------------------------


async def test_health_ready_returns_status(client: AsyncClient) -> None:
    """With test settings (SQLite, in-memory bus), checks should skip."""
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert "checks" in body
    # With SQLite dev and in-memory bus, both should be "skip"
    assert body["checks"]["db"] == "skip"
    assert body["checks"]["redis"] == "skip"


async def test_health_ready_content_type(client: AsyncClient) -> None:
    resp = await client.get("/health/ready")
    assert "application/json" in resp.headers["content-type"]


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


async def test_security_header_nosniff(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"


async def test_security_header_frame_options(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.headers.get("X-Frame-Options") == "DENY"


async def test_security_header_referrer_policy(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


async def test_security_header_permissions_policy(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.headers.get("Permissions-Policy") == "camera=(), microphone=(), geolocation=()"


# ---------------------------------------------------------------------------
# Request ID middleware
# ---------------------------------------------------------------------------


async def test_request_id_generated_when_absent(client: AsyncClient) -> None:
    resp = await client.get("/health")
    rid = resp.headers.get("X-Request-ID")
    assert rid is not None
    assert len(rid) > 0


async def test_request_id_echoed_from_client(client: AsyncClient) -> None:
    custom_id = "my-custom-request-id-123"
    resp = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert resp.headers.get("X-Request-ID") == custom_id


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


def test_create_app_registers_health_ready(settings: Settings) -> None:
    app = create_app(settings=settings)
    route_paths = [r.path for r in app.routes]
    assert "/health/ready" in route_paths


def test_create_app_stores_container(settings: Settings) -> None:
    app = create_app(settings=settings)
    assert hasattr(app.state, "container")
    assert hasattr(app.state, "settings")
    assert app.state.container is not None


async def test_unknown_route_returns_404(client: AsyncClient) -> None:
    resp = await client.get("/nonexistent")
    assert resp.status_code == 404
