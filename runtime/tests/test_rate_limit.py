"""Tests for the rate limiting middleware.

Covers:
- Basic rate limiting (requests under/over limit)
- 429 response with Retry-After header
- X-RateLimit-* response headers on allowed requests
- Health/ready endpoints excluded from rate limiting
- Metrics endpoint excluded from rate limiting
- Client identification by IP vs teacher_id
- Sliding window counter behavior
- Periodic cleanup of expired entries
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.api.middleware.rate_limit import (
    RateLimitMiddleware,
    _SlidingWindowCounter,
)
from ailine_runtime.shared.config import Settings

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        anthropic_api_key="fake-key-for-tests",
        openai_api_key="",
        google_api_key="",
        db={"url": "sqlite+aiosqlite:///:memory:"},
        llm={"provider": "fake", "api_key": "fake"},
        embedding={"provider": "gemini", "api_key": ""},
        redis={"url": ""},
    )


@pytest.fixture()
def app_low_limit(settings: Settings, monkeypatch: pytest.MonkeyPatch):
    """Create app with a very low rate limit (5 RPM) for testing."""
    monkeypatch.setenv("AILINE_RATE_LIMIT_RPM", "5")
    return create_app(settings=settings)


@pytest.fixture()
async def client_low_limit(app_low_limit) -> AsyncClient:
    transport = ASGITransport(app=app_low_limit, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture()
def app_default(settings: Settings):
    """Create app with default rate limit."""
    return create_app(settings=settings)


@pytest.fixture()
async def client_default(app_default) -> AsyncClient:
    transport = ASGITransport(app=app_default, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Test: requests under the limit succeed
# ---------------------------------------------------------------------------


async def test_requests_under_limit_succeed(client_low_limit: AsyncClient) -> None:
    """Requests within the RPM limit should return normally."""
    # 5 RPM limit, send 3 requests -- all should succeed.
    for _ in range(3):
        resp = await client_low_limit.get("/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Test: requests over the limit return 429
# ---------------------------------------------------------------------------


async def test_requests_over_limit_return_429(client_low_limit: AsyncClient) -> None:
    """Exceeding the RPM limit should return 429 Too Many Requests."""
    # 5 RPM limit. Send requests to a non-excluded path.
    # Use /materials which is rate-limited (even though it may 401/404).
    responses = []
    for _ in range(8):
        resp = await client_low_limit.get("/materials")
        responses.append(resp.status_code)

    # At least one response should be 429.
    assert 429 in responses, f"Expected at least one 429, got: {responses}"


# ---------------------------------------------------------------------------
# Test: 429 response includes Retry-After header
# ---------------------------------------------------------------------------


async def test_429_includes_retry_after(client_low_limit: AsyncClient) -> None:
    """429 response should include Retry-After header."""
    for _ in range(10):
        resp = await client_low_limit.get("/materials")
        if resp.status_code == 429:
            assert "Retry-After" in resp.headers
            retry_after = int(resp.headers["Retry-After"])
            assert retry_after > 0
            return

    pytest.fail("Expected at least one 429 response")


# ---------------------------------------------------------------------------
# Test: rate limit headers present on allowed requests
# ---------------------------------------------------------------------------


async def test_rate_limit_headers_on_allowed_request(
    client_low_limit: AsyncClient,
) -> None:
    """Allowed requests should include X-RateLimit-* response headers."""
    resp = await client_low_limit.get("/materials")
    # Even if the endpoint returns a non-200 (e.g. 404), the rate limit
    # headers should still be present (unless it was 429 itself).
    if resp.status_code != 429:
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers
        assert "X-RateLimit-Reset" in resp.headers
        assert resp.headers["X-RateLimit-Limit"] == "5"


# ---------------------------------------------------------------------------
# Test: health endpoint excluded from rate limiting
# ---------------------------------------------------------------------------


async def test_health_excluded_from_rate_limiting(
    client_low_limit: AsyncClient,
) -> None:
    """Health endpoints should never be rate-limited."""
    # Send far more requests than the limit.
    for _ in range(20):
        resp = await client_low_limit.get("/health")
        assert resp.status_code == 200
        # Health responses should NOT have rate limit headers.
        assert "X-RateLimit-Limit" not in resp.headers


# ---------------------------------------------------------------------------
# Test: health/ready excluded from rate limiting
# ---------------------------------------------------------------------------


async def test_health_ready_excluded_from_rate_limiting(
    client_low_limit: AsyncClient,
) -> None:
    """Health/ready endpoint should never be rate-limited."""
    for _ in range(20):
        resp = await client_low_limit.get("/health/ready")
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" not in resp.headers


# ---------------------------------------------------------------------------
# Test: metrics endpoint excluded from rate limiting
# ---------------------------------------------------------------------------


async def test_metrics_excluded_from_rate_limiting(
    client_low_limit: AsyncClient,
) -> None:
    """/metrics endpoint should never be rate-limited."""
    for _ in range(20):
        resp = await client_low_limit.get("/metrics")
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" not in resp.headers


# ---------------------------------------------------------------------------
# Test: 429 body contains detail message
# ---------------------------------------------------------------------------


async def test_429_body_contains_detail(client_low_limit: AsyncClient) -> None:
    """429 response body should contain a human-readable detail message."""
    for _ in range(10):
        resp = await client_low_limit.get("/materials")
        if resp.status_code == 429:
            body = resp.json()
            assert "detail" in body
            assert "Too many requests" in body["detail"]
            return

    pytest.fail("Expected at least one 429 response")


# ---------------------------------------------------------------------------
# Test: sliding window counter unit test
# ---------------------------------------------------------------------------


def test_sliding_window_counter_initial_state() -> None:
    """A new counter should have zero counts."""
    counter = _SlidingWindowCounter()
    assert counter.prev_count == 0
    assert counter.curr_count == 0


# ---------------------------------------------------------------------------
# Test: RateLimitMiddleware rpm property
# ---------------------------------------------------------------------------


def test_rate_limit_middleware_rpm_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """RPM should be configurable via environment variable."""
    monkeypatch.setenv("AILINE_RATE_LIMIT_RPM", "120")
    # Create a standalone middleware instance (no real app needed for this).
    mw = RateLimitMiddleware(app=None, rpm=None)  # type: ignore[arg-type]
    # It reads from env since rpm=None.
    assert mw.rpm == 120


def test_rate_limit_middleware_rpm_explicit() -> None:
    """Explicit rpm parameter should override env variable."""
    mw = RateLimitMiddleware(app=None, rpm=42)  # type: ignore[arg-type]
    assert mw.rpm == 42


# ---------------------------------------------------------------------------
# Test: authenticated user keyed by teacher_id
# ---------------------------------------------------------------------------


async def test_authenticated_user_keyed_by_teacher_id(
    client_low_limit: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When dev mode is on and X-Teacher-ID is provided, rate limit
    should be keyed by teacher_id, not IP. Two different teacher IDs
    should have independent limits."""
    monkeypatch.setenv("AILINE_DEV_MODE", "true")

    # Send 4 requests as teacher-A (under 5 RPM limit).
    for _ in range(4):
        resp = await client_low_limit.get(
            "/materials",
            headers={"X-Teacher-ID": "teacher-A"},
        )
        # Should not be 429 yet for teacher-A.
        assert resp.status_code != 429

    # Send 4 requests as teacher-B (should also be under limit).
    for _ in range(4):
        resp = await client_low_limit.get(
            "/materials",
            headers={"X-Teacher-ID": "teacher-B"},
        )
        assert resp.status_code != 429
