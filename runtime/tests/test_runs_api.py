"""Tests for the /runs API (F-237 Run Resource Model).

Covers: listing, detail, status filtering, pagination, tenant isolation.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.shared.config import Settings
from ailine_runtime.shared.trace_store import get_trace_store, reset_trace_store


@pytest.fixture(autouse=True)
def _reset_store() -> None:
    reset_trace_store()


@pytest.fixture()
def app(settings: Settings, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    return create_app(settings=settings)


@pytest.fixture()
async def client(app) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Teacher-ID": "teacher-runs-001"},
    ) as c:
        yield c


async def _seed_runs(teacher_id: str = "teacher-runs-001") -> None:
    """Seed the trace store with sample runs."""
    store = get_trace_store()
    for i, status in enumerate(["completed", "completed", "running", "failed"]):
        run_id = f"run-{i:03d}"
        await store.get_or_create(run_id, teacher_id=teacher_id)
        await store.update_run(
            run_id,
            status=status,
            user_prompt=f"Create a lesson about topic {i}",
            subject=f"Subject-{i}",
            total_time_ms=1000.0 + i * 100,
            final_score=80 + i if status == "completed" else None,
        )


# ---------------------------------------------------------------------------
# GET /runs
# ---------------------------------------------------------------------------


class TestListRuns:
    async def test_empty_list(self, client: AsyncClient) -> None:
        resp = await client.get("/runs")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    async def test_list_returns_seeded_runs(self, client: AsyncClient) -> None:
        await _seed_runs()
        resp = await client.get("/runs")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 4
        assert len(body["items"]) == 4

    async def test_list_has_required_fields(self, client: AsyncClient) -> None:
        await _seed_runs()
        body = (await client.get("/runs")).json()
        item = body["items"][0]
        assert "run_id" in item
        assert "status" in item
        assert "created_at" in item
        assert "user_prompt" in item
        assert "subject" in item
        assert "total_time_ms" in item
        assert "final_score" in item
        assert "node_count" in item

    async def test_filter_by_status(self, client: AsyncClient) -> None:
        await _seed_runs()
        resp = await client.get("/runs", params={"status": "completed"})
        body = resp.json()
        assert body["total"] == 2
        assert all(item["status"] == "completed" for item in body["items"])

    async def test_filter_running(self, client: AsyncClient) -> None:
        await _seed_runs()
        resp = await client.get("/runs", params={"status": "running"})
        body = resp.json()
        assert body["total"] == 1

    async def test_filter_failed(self, client: AsyncClient) -> None:
        await _seed_runs()
        resp = await client.get("/runs", params={"status": "failed"})
        body = resp.json()
        assert body["total"] == 1

    async def test_pagination_limit(self, client: AsyncClient) -> None:
        await _seed_runs()
        resp = await client.get("/runs", params={"limit": 2})
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["total"] == 4
        assert body["limit"] == 2

    async def test_pagination_offset(self, client: AsyncClient) -> None:
        await _seed_runs()
        resp = await client.get("/runs", params={"limit": 2, "offset": 2})
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["offset"] == 2

    async def test_tenant_isolation(self, client: AsyncClient) -> None:
        """Runs from other teachers should not be visible."""
        await _seed_runs(teacher_id="other-teacher")
        resp = await client.get("/runs")
        body = resp.json()
        assert body["total"] == 0

    async def test_requires_auth(self, app) -> None:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/runs")
            assert resp.status_code in (401, 403)

    async def test_invalid_status_filter(self, client: AsyncClient) -> None:
        resp = await client.get("/runs", params={"status": "invalid"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /runs/{run_id}
# ---------------------------------------------------------------------------


class TestGetRun:
    async def test_get_existing_run(self, client: AsyncClient) -> None:
        await _seed_runs()
        resp = await client.get("/runs/run-000")
        assert resp.status_code == 200
        body = resp.json()
        assert body["run_id"] == "run-000"
        assert body["status"] == "completed"
        assert body["user_prompt"] == "Create a lesson about topic 0"
        assert body["subject"] == "Subject-0"

    async def test_get_nonexistent_run(self, client: AsyncClient) -> None:
        resp = await client.get("/runs/nonexistent")
        assert resp.status_code == 404

    async def test_get_run_tenant_isolation(self, client: AsyncClient) -> None:
        """Cannot access another teacher's run."""
        await _seed_runs(teacher_id="other-teacher")
        resp = await client.get("/runs/run-000")
        assert resp.status_code == 404

    async def test_get_run_has_full_trace(self, client: AsyncClient) -> None:
        await _seed_runs()
        body = (await client.get("/runs/run-000")).json()
        assert "nodes" in body
        assert "scorecard" in body
        assert "created_at" in body

    async def test_created_at_is_iso_timestamp(self, client: AsyncClient) -> None:
        await _seed_runs()
        body = (await client.get("/runs/run-000")).json()
        assert body["created_at"]  # non-empty
        assert "T" in body["created_at"]  # ISO format
