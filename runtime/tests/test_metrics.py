"""Tests for the lightweight metrics module and /metrics endpoint.

Covers:
- Counter increment and label support
- Histogram observation and bucket distribution
- Prometheus text format rendering
- /metrics endpoint returns valid text format
- Pre-defined metrics are incremented by HTTP requests
- HTTP request duration is recorded
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import Settings
from ailine_runtime.shared.metrics import (
    Counter,
    Histogram,
    render_metrics,
)

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
def app(settings: Settings):
    return create_app(settings=settings)


@pytest.fixture()
async def client(app) -> AsyncClient:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Test: Counter basic increment
# ---------------------------------------------------------------------------


def test_counter_increment() -> None:
    """Counter should increment and return correct value."""
    c = Counter("test_counter", "A test counter")
    assert c.get(method="GET") == 0.0
    c.inc(method="GET")
    assert c.get(method="GET") == 1.0
    c.inc(value=5.0, method="GET")
    assert c.get(method="GET") == 6.0


# ---------------------------------------------------------------------------
# Test: Counter label isolation
# ---------------------------------------------------------------------------


def test_counter_label_isolation() -> None:
    """Different label sets should have independent counts."""
    c = Counter("test_counter_labels", "Label isolation test")
    c.inc(method="GET", path="/a")
    c.inc(method="GET", path="/a")
    c.inc(method="POST", path="/b")

    assert c.get(method="GET", path="/a") == 2.0
    assert c.get(method="POST", path="/b") == 1.0
    assert c.get(method="DELETE", path="/c") == 0.0


# ---------------------------------------------------------------------------
# Test: Counter collect returns all label sets
# ---------------------------------------------------------------------------


def test_counter_collect() -> None:
    """collect() should return all label-set / value pairs."""
    c = Counter("test_collect", "Collect test")
    c.inc(method="GET")
    c.inc(method="POST")
    c.inc(method="GET")

    result = c.collect()
    assert len(result) == 2
    values_by_method = {d["method"]: v for d, v in result}
    assert values_by_method["GET"] == 2.0
    assert values_by_method["POST"] == 1.0


# ---------------------------------------------------------------------------
# Test: Histogram observation and buckets
# ---------------------------------------------------------------------------


def test_histogram_observe() -> None:
    """Histogram should correctly distribute values into buckets."""
    h = Histogram("test_hist", "Test histogram", buckets=[0.1, 0.5, 1.0])
    h.observe(0.05, method="GET")  # fits in 0.1, 0.5, 1.0
    h.observe(0.3, method="GET")   # fits in 0.5, 1.0
    h.observe(0.8, method="GET")   # fits in 1.0
    h.observe(2.0, method="GET")   # does not fit in any bucket

    result = h.collect()
    assert len(result) == 1
    labels, data = result[0]
    assert labels == {"method": "GET"}
    assert data["_count"] == 4
    assert data["_sum"] == pytest.approx(3.15)
    assert data["buckets"][0.1] == 1
    assert data["buckets"][0.5] == 2
    assert data["buckets"][1.0] == 3


# ---------------------------------------------------------------------------
# Test: Prometheus text format rendering
# ---------------------------------------------------------------------------


def test_render_metrics_format() -> None:
    """render_metrics() should return valid Prometheus text format."""
    text = render_metrics()
    assert isinstance(text, str)
    # Should contain HELP and TYPE lines for predefined metrics.
    assert "# HELP ailine_http_requests_total" in text
    assert "# TYPE ailine_http_requests_total counter" in text
    assert "# HELP ailine_http_request_duration_seconds" in text
    assert "# TYPE ailine_http_request_duration_seconds histogram" in text
    assert "# HELP ailine_llm_calls_total" in text
    assert "# TYPE ailine_llm_calls_total counter" in text


# ---------------------------------------------------------------------------
# Test: /metrics endpoint returns text format
# ---------------------------------------------------------------------------


async def test_metrics_endpoint_returns_prometheus_text(
    client: AsyncClient,
) -> None:
    """/metrics should return Prometheus text format with correct content type."""
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "ailine_http_requests_total" in body


# ---------------------------------------------------------------------------
# Test: HTTP requests increment counter
# ---------------------------------------------------------------------------


async def test_http_request_increments_counter(client: AsyncClient) -> None:
    """Making HTTP requests should increment the http_requests_total counter."""
    # Make a known request.
    await client.get("/health")

    # Fetch metrics and verify the counter was incremented.
    resp = await client.get("/metrics")
    body = resp.text
    # Should contain a counter entry for GET /health with status 200.
    assert 'ailine_http_requests_total{method="GET",path="/health",status="200"}' in body


# ---------------------------------------------------------------------------
# Test: HTTP request duration is recorded
# ---------------------------------------------------------------------------


async def test_http_request_duration_recorded(client: AsyncClient) -> None:
    """Making HTTP requests should record duration in the histogram."""
    await client.get("/health")

    resp = await client.get("/metrics")
    body = resp.text
    # Should contain histogram bucket entries for /health.
    assert "ailine_http_request_duration_seconds_bucket" in body
    assert "ailine_http_request_duration_seconds_sum" in body
    assert "ailine_http_request_duration_seconds_count" in body
