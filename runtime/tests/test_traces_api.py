"""Tests for the traces API router."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.domain.entities.trace import NodeTrace, RouteRationale
from ailine_runtime.shared.config import Settings
from ailine_runtime.shared.trace_store import get_trace_store, reset_trace_store


@pytest.fixture(autouse=True)
def _reset():
    reset_trace_store()
    yield
    reset_trace_store()


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    settings = Settings(env="development")
    return create_app(settings)


_AUTH = {"X-Teacher-ID": "teacher-test"}


class TestTracesAPI:
    """GET /traces endpoints."""

    @pytest.mark.asyncio
    async def test_get_trace_not_found(self, app) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_AUTH,
        ) as client:
            resp = await client.get("/traces/nonexistent")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_trace_found(self, app) -> None:
        store = get_trace_store()
        await store.get_or_create("run-42")
        await store.append_node(
            "run-42",
            NodeTrace(node="planner", status="success", time_ms=100.0),
        )
        await store.update_run("run-42", status="completed", total_time_ms=200.0)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_AUTH,
        ) as client:
            resp = await client.get("/traces/run-42")
            assert resp.status_code == 200
            data = resp.json()
            assert data["run_id"] == "run-42"
            assert data["status"] == "completed"
            assert len(data["nodes"]) == 1
            assert data["nodes"][0]["node"] == "planner"
            assert data["nodes"][0]["time_ms"] == 100.0

    @pytest.mark.asyncio
    async def test_get_trace_with_rationale(self, app) -> None:
        store = get_trace_store()
        await store.append_node(
            "run-99",
            NodeTrace(
                node="planner",
                status="success",
                time_ms=150.0,
                route_rationale=RouteRationale(
                    task_type="planner",
                    tier="primary",
                    model_selected="claude-opus-4-6",
                    reason="SmartRouter primary tier",
                    composite_score=0.8,
                    weighted_scores={"token": 0.25, "structured": 0.25},
                ),
            ),
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_AUTH,
        ) as client:
            resp = await client.get("/traces/run-99")
            assert resp.status_code == 200
            data = resp.json()
            node = data["nodes"][0]
            assert node["route_rationale"] is not None
            assert node["route_rationale"]["tier"] == "primary"
            assert node["route_rationale"]["model_selected"] == "claude-opus-4-6"

    @pytest.mark.asyncio
    async def test_list_recent_empty(self, app) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_AUTH,
        ) as client:
            resp = await client.get("/traces/recent")
            assert resp.status_code == 200
            assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_recent_with_data(self, app) -> None:
        store = get_trace_store()
        await store.get_or_create("run-1")
        await store.update_run("run-1", status="completed", total_time_ms=100.0, final_score=85)
        await store.get_or_create("run-2")
        await store.update_run("run-2", status="completed", total_time_ms=200.0, final_score=72)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_AUTH,
        ) as client:
            resp = await client.get("/traces/recent?limit=10")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
            # Each entry has expected fields
            for entry in data:
                assert "run_id" in entry
                assert "status" in entry
                assert "total_time_ms" in entry
                assert "final_score" in entry
