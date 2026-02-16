"""Tests for the observability dashboard API."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.domain.entities.trace import NodeTrace, RouteRationale
from ailine_runtime.shared.config import Settings
from ailine_runtime.shared.observability_store import (
    get_observability_store,
    reset_observability_store,
)
from ailine_runtime.shared.trace_store import get_trace_store, reset_trace_store


@pytest.fixture(autouse=True)
def _reset():
    reset_trace_store()
    reset_observability_store()
    yield
    reset_trace_store()
    reset_observability_store()


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AILINE_DEV_MODE", "true")
    settings = Settings(env="development")
    return create_app(settings)


def _auth_headers() -> dict[str, str]:
    return {"X-Teacher-ID": "teacher-test"}


class TestObservabilityDashboard:
    """GET /observability/dashboard."""

    @pytest.mark.asyncio
    async def test_dashboard_empty(self, app) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_auth_headers(),
        ) as client:
            resp = await client.get("/observability/dashboard")
            assert resp.status_code == 200
            data = resp.json()
            assert "llm" in data
            assert "circuit_breaker" in data
            assert "http" in data
            assert "sse" in data
            assert "tokens" in data
            assert "smart_router" in data
            assert "pipeline" in data

    @pytest.mark.asyncio
    async def test_dashboard_with_trace_data(self, app) -> None:
        store = get_trace_store()
        await store.get_or_create("run-1", teacher_id="teacher-test")
        await store.append_node(
            "run-1",
            NodeTrace(
                node="planner",
                status="success",
                time_ms=100.0,
                route_rationale=RouteRationale(
                    task_type="planner",
                    tier="primary",
                    model_selected="claude-opus-4-6",
                    weighted_scores={"token": 0.25},
                ),
            ),
        )
        await store.update_run("run-1", status="completed")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_auth_headers(),
        ) as client:
            resp = await client.get("/observability/dashboard")
            assert resp.status_code == 200
            data = resp.json()
            assert data["pipeline"]["recent_runs"] >= 1
            assert data["pipeline"]["completed"] >= 1
            decisions = data["smart_router"]["recent_decisions"]
            assert len(decisions) >= 1
            assert decisions[0]["tier"] == "primary"

    @pytest.mark.asyncio
    async def test_dashboard_with_sse_and_tokens(self, app) -> None:
        obs = get_observability_store()
        obs.record_sse_event("stage.started")
        obs.record_sse_event("stage.started")
        obs.record_sse_event("stage.completed")
        obs.record_tokens(input_tokens=500, output_tokens=200, model="claude-haiku-4-5")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_auth_headers(),
        ) as client:
            resp = await client.get("/observability/dashboard")
            assert resp.status_code == 200
            data = resp.json()
            assert data["sse"]["event_counts"]["stage.started"] == 2
            assert data["sse"]["event_counts"]["stage.completed"] == 1
            assert data["tokens"]["input_tokens"] == 500
            assert data["tokens"]["output_tokens"] == 200
            assert data["tokens"]["estimated_cost_usd"] > 0


class TestStandardsEvidence:
    """GET /observability/standards-evidence/{run_id}."""

    @pytest.mark.asyncio
    async def test_not_found(self, app) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_auth_headers(),
        ) as client:
            resp = await client.get("/observability/standards-evidence/nonexistent")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_with_evidence(self, app) -> None:
        store = get_trace_store()
        await store.get_or_create("run-42", teacher_id="teacher-test")
        await store.update_run("run-42", status="completed", final_score=85)

        obs = get_observability_store()
        obs.record_standards_evidence(
            run_id="run-42",
            standards=[
                {"code": "EF06MA01", "system": "bncc", "description": "Fractions"},
                {
                    "code": "CCSS.MATH.6.NS.A.1",
                    "system": "ccss",
                    "description": "Division",
                },
            ],
            bloom_level="apply",
            alignment_explanation=(
                "This lesson addresses fraction operations (BNCC EF06MA01) "
                "and division of fractions (CCSS 6.NS.A.1) at the Apply level."
            ),
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_auth_headers(),
        ) as client:
            resp = await client.get("/observability/standards-evidence/run-42")
            assert resp.status_code == 200
            data = resp.json()
            assert data["run_id"] == "run-42"
            assert data["final_score"] == 85
            assert len(data["standards"]) == 2
            assert data["bloom_level"] == "apply"
            assert "BNCC" in data["alignment_explanation"]
            assert data["handout_available"] is True


class TestStandardsHandout:
    """GET /observability/standards-evidence/{run_id}/handout."""

    @pytest.mark.asyncio
    async def test_not_found(self, app) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_auth_headers(),
        ) as client:
            resp = await client.get(
                "/observability/standards-evidence/nonexistent/handout"
            )
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_handout_format(self, app) -> None:
        store = get_trace_store()
        await store.get_or_create("run-99", teacher_id="teacher-test")
        await store.append_node(
            "run-99",
            NodeTrace(
                node="validate",
                status="success",
                time_ms=50.0,
                quality_score=90,
                outputs_summary={"quality_status": "accept"},
            ),
        )
        await store.update_run("run-99", status="completed")

        obs = get_observability_store()
        obs.record_standards_evidence(
            run_id="run-99",
            standards=[{"code": "NGSS-MS-PS1-1", "system": "ngss"}],
            bloom_level="analyze",
            alignment_explanation="Aligned with Matter and Interactions.",
        )

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers=_auth_headers(),
        ) as client:
            resp = await client.get("/observability/standards-evidence/run-99/handout")
            assert resp.status_code == 200
            data = resp.json()
            assert data["type"] == "teacher_handout"
            assert data["run_id"] == "run-99"
            assert data["quality"]["score"] == 90
            assert len(data["pipeline_nodes"]) == 1
            assert data["generated_by"] == "AiLine Adaptive Inclusive Learning Platform"


class TestObservabilityStore:
    """Unit tests for the ObservabilityStore."""

    def test_sse_event_counting(self) -> None:
        obs = get_observability_store()
        obs.record_sse_event("run.started")
        obs.record_sse_event("run.started")
        obs.record_sse_event("run.completed")
        counts = obs.get_sse_event_counts()
        assert counts["run.started"] == 2
        assert counts["run.completed"] == 1

    def test_token_cost_estimate(self) -> None:
        obs = get_observability_store()
        obs.record_tokens(
            input_tokens=1000, output_tokens=500, model="claude-haiku-4-5"
        )
        stats = obs.get_token_stats()
        assert stats["input_tokens"] == 1000
        assert stats["output_tokens"] == 500
        assert stats["total_tokens"] == 1500
        assert stats["estimated_cost_usd"] > 0
        assert stats["cost_breakdown"]["model"] == "claude-haiku-4-5"

    def test_provider_status(self) -> None:
        obs = get_observability_store()
        obs.update_provider_status("anthropic", "claude-opus-4-6", "healthy")
        status = obs.get_provider_status()
        assert status["name"] == "anthropic"
        assert status["model"] == "claude-opus-4-6"
        assert status["status"] == "healthy"

    def test_circuit_breaker_state(self) -> None:
        obs = get_observability_store()
        obs.update_circuit_breaker_state("open")
        assert obs.get_circuit_breaker_state() == "open"

    def test_standards_evidence(self) -> None:
        obs = get_observability_store()
        obs.record_standards_evidence(
            "run-1",
            standards=[{"code": "EF06MA01"}],
            bloom_level="understand",
            alignment_explanation="Aligned with BNCC.",
        )
        ev = obs.get_standards_evidence("run-1")
        assert len(ev["standards"]) == 1
        assert ev["bloom_level"] == "understand"

    def test_standards_evidence_missing(self) -> None:
        obs = get_observability_store()
        ev = obs.get_standards_evidence("nonexistent")
        assert ev["standards"] == []
        assert ev["bloom_level"] is None
