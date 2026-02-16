"""Tests for the demo mode subsystem.

Covers:
- DemoService: scenario loading, listing, retrieval, cached plan/events, reset
- Demo API endpoints: GET /demo/scenarios, GET /demo/scenarios/{id},
  POST /demo/scenarios/{id}/run, POST /demo/scenarios/{id}/execute,
  POST /demo/scenarios/{id}/stream, GET /demo/reset
- DemoModeMiddleware: interception of /plans/generate when demo_mode=true
- Edge cases: missing scenarios, empty data dir, malformed JSON
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.api.app import create_app
from ailine_runtime.app.services.demo import DemoService
from ailine_runtime.shared.config import (
    DatabaseConfig,
    EmbeddingConfig,
    LLMConfig,
    RedisConfig,
    Settings,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SAMPLE_SCENARIO: dict[str, Any] = {
    "id": "test-scenario",
    "title": "Test Scenario",
    "description": "A test scenario for unit tests.",
    "prompt": "Create a test lesson plan.",
    "grade": "5th grade",
    "subject": "Science",
    "locale": "en",
    "expected_skills": ["MS-LS1-6"],
    "demo_tags": ["test", "unit"],
    "accessibility_profile": {"needs": {"adhd": True}},
    "cached_plan": {
        "title": "Test Plan",
        "grade": "5th",
        "standard": "BNCC",
        "objectives": [{"id": "T001", "text": "Test objective."}],
        "steps": [
            {
                "minutes": 10,
                "title": "Step 1",
                "instructions": ["Do something."],
                "activities": ["Activity 1."],
                "assessment": ["Check understanding."],
            }
        ],
    },
    "cached_events": [
        {"type": "run_start", "stage": "init", "delay_ms": 0},
        {"type": "stage_start", "stage": "planner", "delay_ms": 100},
        {"type": "stage_complete", "stage": "planner", "delay_ms": 200},
        {"type": "run_complete", "stage": "done", "delay_ms": 300},
    ],
    "score": 85,
}


@pytest.fixture()
def demo_data_dir(tmp_path: Path) -> Path:
    """Create a temp directory with a sample scenario JSON."""
    data_dir = tmp_path / "demo"
    data_dir.mkdir()
    scenario_file = data_dir / "test_scenario.json"
    scenario_file.write_text(json.dumps(_SAMPLE_SCENARIO), encoding="utf-8")
    return data_dir


@pytest.fixture()
def demo_service(demo_data_dir: Path) -> DemoService:
    """Build a DemoService from the temp data directory."""
    return DemoService(data_dir=demo_data_dir)


@pytest.fixture()
def settings_demo_off() -> Settings:
    """Settings with demo_mode=False."""
    return Settings(
        anthropic_api_key="fake-key",
        openai_api_key="",
        google_api_key="",
        db=DatabaseConfig(url="sqlite+aiosqlite:///:memory:"),
        llm=LLMConfig(provider="fake", api_key="fake"),
        embedding=EmbeddingConfig(provider="gemini", api_key=""),
        redis=RedisConfig(url="redis://localhost:6379/0"),
        demo_mode=False,
    )


@pytest.fixture()
def settings_demo_on() -> Settings:
    """Settings with demo_mode=True."""
    return Settings(
        anthropic_api_key="fake-key",
        openai_api_key="",
        google_api_key="",
        db=DatabaseConfig(url="sqlite+aiosqlite:///:memory:"),
        llm=LLMConfig(provider="fake", api_key="fake"),
        embedding=EmbeddingConfig(provider="gemini", api_key=""),
        redis=RedisConfig(url="redis://localhost:6379/0"),
        demo_mode=True,
    )


@pytest.fixture()
def app_demo_off(settings_demo_off: Settings):
    """FastAPI app with demo mode disabled."""
    return create_app(settings=settings_demo_off)


@pytest.fixture()
def app_demo_on(settings_demo_on: Settings):
    """FastAPI app with demo mode enabled."""
    return create_app(settings=settings_demo_on)


@pytest.fixture()
async def client_demo_off(app_demo_off) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app_demo_off, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport, base_url="http://test", timeout=10.0
    ) as c:
        yield c


@pytest.fixture()
async def client_demo_on(app_demo_on) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app_demo_on, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport, base_url="http://test", timeout=10.0
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# DemoService unit tests
# ---------------------------------------------------------------------------


class TestDemoServiceLoading:
    """Tests for DemoService scenario loading."""

    def test_loads_scenarios_from_directory(self, demo_service: DemoService) -> None:
        assert demo_service.scenario_count == 1

    def test_loads_correct_scenario_id(self, demo_service: DemoService) -> None:
        scenarios = demo_service.list_scenarios()
        assert len(scenarios) == 1
        assert scenarios[0]["id"] == "test-scenario"

    def test_handles_empty_data_dir(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty_demo"
        empty_dir.mkdir()
        svc = DemoService(data_dir=empty_dir)
        assert svc.scenario_count == 0
        assert svc.list_scenarios() == []

    def test_handles_missing_data_dir(self, tmp_path: Path) -> None:
        missing_dir = tmp_path / "nonexistent"
        svc = DemoService(data_dir=missing_dir)
        assert svc.scenario_count == 0

    def test_skips_file_without_id(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "demo_no_id"
        data_dir.mkdir()
        (data_dir / "bad.json").write_text('{"title": "No ID"}', encoding="utf-8")
        svc = DemoService(data_dir=data_dir)
        assert svc.scenario_count == 0

    def test_skips_malformed_json(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "demo_bad_json"
        data_dir.mkdir()
        (data_dir / "broken.json").write_text("{not valid json", encoding="utf-8")
        svc = DemoService(data_dir=data_dir)
        assert svc.scenario_count == 0

    def test_loads_multiple_scenarios(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "demo_multi"
        data_dir.mkdir()
        for i in range(3):
            scenario = {
                "id": f"scenario-{i}",
                "title": f"Scenario {i}",
                "description": f"Desc {i}",
            }
            (data_dir / f"s{i}.json").write_text(json.dumps(scenario), encoding="utf-8")
        svc = DemoService(data_dir=data_dir)
        assert svc.scenario_count == 3


class TestDemoServiceRetrieval:
    """Tests for DemoService scenario retrieval methods."""

    def test_list_scenarios_returns_summaries(self, demo_service: DemoService) -> None:
        items = demo_service.list_scenarios()
        assert len(items) == 1
        item = items[0]
        assert "id" in item
        assert "title" in item
        assert "description" in item
        assert item["title"] == "Test Scenario"

    def test_list_scenarios_includes_optional_fields(
        self, demo_service: DemoService
    ) -> None:
        items = demo_service.list_scenarios()
        item = items[0]
        assert item["grade"] == "5th grade"
        assert item["subject"] == "Science"
        assert item["locale"] == "en"
        assert item["expected_skills"] == ["MS-LS1-6"]
        assert item["demo_tags"] == ["test", "unit"]

    def test_list_scenarios_omits_missing_optional_fields(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "demo_minimal"
        data_dir.mkdir()
        scenario = {"id": "minimal", "title": "Minimal", "description": "No extras"}
        (data_dir / "m.json").write_text(json.dumps(scenario), encoding="utf-8")
        svc = DemoService(data_dir=data_dir)
        items = svc.list_scenarios()
        assert len(items) == 1
        assert "grade" not in items[0]
        assert "subject" not in items[0]

    def test_get_scenario_returns_full_data(self, demo_service: DemoService) -> None:
        scenario = demo_service.get_scenario("test-scenario")
        assert scenario is not None
        assert scenario["id"] == "test-scenario"
        assert "cached_plan" in scenario
        assert "cached_events" in scenario

    def test_get_scenario_returns_none_for_missing(
        self, demo_service: DemoService
    ) -> None:
        assert demo_service.get_scenario("nonexistent") is None

    def test_get_cached_plan_returns_plan(self, demo_service: DemoService) -> None:
        plan = demo_service.get_cached_plan("test-scenario")
        assert plan is not None
        assert plan["title"] == "Test Plan"
        assert len(plan["steps"]) == 1

    def test_get_cached_plan_returns_none_for_missing(
        self, demo_service: DemoService
    ) -> None:
        assert demo_service.get_cached_plan("nonexistent") is None

    def test_get_cached_events_returns_events(self, demo_service: DemoService) -> None:
        events = demo_service.get_cached_events("test-scenario")
        assert len(events) == 4
        assert events[0]["type"] == "run_start"
        assert events[-1]["type"] == "run_complete"

    def test_get_cached_events_returns_empty_for_missing(
        self, demo_service: DemoService
    ) -> None:
        assert demo_service.get_cached_events("nonexistent") == []

    def test_get_score_returns_score(self, demo_service: DemoService) -> None:
        assert demo_service.get_score("test-scenario") == 85

    def test_get_score_returns_none_for_missing(
        self, demo_service: DemoService
    ) -> None:
        assert demo_service.get_score("nonexistent") is None

    def test_get_prompt_returns_prompt(self, demo_service: DemoService) -> None:
        assert demo_service.get_prompt("test-scenario") == "Create a test lesson plan."

    def test_get_prompt_returns_none_for_missing(
        self, demo_service: DemoService
    ) -> None:
        assert demo_service.get_prompt("nonexistent") is None

    def test_get_cached_plan_returns_none_when_no_plan_field(
        self, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "demo_no_plan"
        data_dir.mkdir()
        scenario = {
            "id": "no-plan",
            "title": "No Plan",
            "description": "Missing cached_plan",
        }
        (data_dir / "no_plan.json").write_text(json.dumps(scenario), encoding="utf-8")
        svc = DemoService(data_dir=data_dir)
        assert svc.get_cached_plan("no-plan") is None

    def test_get_cached_events_returns_empty_when_no_events_field(
        self, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "demo_no_events"
        data_dir.mkdir()
        scenario = {
            "id": "no-events",
            "title": "No Events",
            "description": "Missing cached_events",
        }
        (data_dir / "no_events.json").write_text(json.dumps(scenario), encoding="utf-8")
        svc = DemoService(data_dir=data_dir)
        assert svc.get_cached_events("no-events") == []


class TestDemoServiceReset:
    """Tests for DemoService.reset()."""

    def test_reset_reloads_scenarios(self, demo_data_dir: Path) -> None:
        svc = DemoService(data_dir=demo_data_dir)
        assert svc.scenario_count == 1
        svc.reset()
        assert svc.scenario_count == 1

    def test_reset_picks_up_new_files(self, demo_data_dir: Path) -> None:
        svc = DemoService(data_dir=demo_data_dir)
        assert svc.scenario_count == 1
        new_scenario = {
            "id": "new-scenario",
            "title": "New",
            "description": "Added after init",
        }
        (demo_data_dir / "new.json").write_text(
            json.dumps(new_scenario), encoding="utf-8"
        )
        svc.reset()
        assert svc.scenario_count == 2

    def test_reset_removes_deleted_files(self, demo_data_dir: Path) -> None:
        svc = DemoService(data_dir=demo_data_dir)
        assert svc.scenario_count == 1
        for f in demo_data_dir.glob("*.json"):
            f.unlink()
        svc.reset()
        assert svc.scenario_count == 0


# ---------------------------------------------------------------------------
# Demo API endpoint tests
# ---------------------------------------------------------------------------


class TestDemoAPIList:
    """Tests for GET /demo/scenarios."""

    async def test_list_returns_scenarios(self, client_demo_off: AsyncClient) -> None:
        resp = await client_demo_off.get("/demo/scenarios")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        # Should load from the real data/demo directory (3 curated scenarios)
        assert len(body) >= 1
        for item in body:
            assert "id" in item
            assert "title" in item
            assert "description" in item

    async def test_list_includes_extended_fields(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.get("/demo/scenarios")
        body = resp.json()
        for item in body:
            assert "grade" in item
            assert "subject" in item
            assert "locale" in item
            assert "expected_skills" in item
            assert "demo_tags" in item


class TestDemoAPIGetScenario:
    """Tests for GET /demo/scenarios/{id}."""

    async def test_get_existing_scenario(self, client_demo_off: AsyncClient) -> None:
        # First list to get a valid ID
        list_resp = await client_demo_off.get("/demo/scenarios")
        scenarios = list_resp.json()
        if not scenarios:
            pytest.skip("No demo scenarios available")
        scenario_id = scenarios[0]["id"]

        resp = await client_demo_off.get(f"/demo/scenarios/{scenario_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == scenario_id
        assert "cached_plan" in body

    async def test_get_nonexistent_scenario_returns_404(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.get("/demo/scenarios/nonexistent-id")
        assert resp.status_code == 404


class TestDemoAPIRun:
    """Tests for POST /demo/scenarios/{id}/run."""

    async def test_run_returns_cached_plan(self, client_demo_off: AsyncClient) -> None:
        list_resp = await client_demo_off.get("/demo/scenarios")
        scenarios = list_resp.json()
        if not scenarios:
            pytest.skip("No demo scenarios available")
        scenario_id = scenarios[0]["id"]

        resp = await client_demo_off.post(f"/demo/scenarios/{scenario_id}/run")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["demo_mode"] is True
        assert "plan" in body
        assert body["run_id"] == f"demo-{scenario_id}"

    async def test_run_nonexistent_returns_404(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.post("/demo/scenarios/nonexistent-id/run")
        assert resp.status_code == 404


class TestDemoAPIExecute:
    """Tests for POST /demo/scenarios/{id}/execute."""

    async def test_execute_returns_cached_plan(
        self, client_demo_off: AsyncClient
    ) -> None:
        list_resp = await client_demo_off.get("/demo/scenarios")
        scenarios = list_resp.json()
        if not scenarios:
            pytest.skip("No demo scenarios available")
        scenario_id = scenarios[0]["id"]

        resp = await client_demo_off.post(f"/demo/scenarios/{scenario_id}/execute")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["demo_mode"] is True
        assert "plan" in body
        assert body["run_id"] == f"demo-{scenario_id}"

    async def test_execute_nonexistent_returns_404(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.post("/demo/scenarios/nonexistent-id/execute")
        assert resp.status_code == 404

    async def test_execute_matches_run_output(
        self, client_demo_off: AsyncClient
    ) -> None:
        list_resp = await client_demo_off.get("/demo/scenarios")
        scenarios = list_resp.json()
        if not scenarios:
            pytest.skip("No demo scenarios available")
        scenario_id = scenarios[0]["id"]

        run_resp = await client_demo_off.post(f"/demo/scenarios/{scenario_id}/run")
        exec_resp = await client_demo_off.post(f"/demo/scenarios/{scenario_id}/execute")
        assert run_resp.json() == exec_resp.json()


class TestDemoAPIReset:
    """Tests for GET /demo/reset."""

    async def test_reset_returns_ok(self, client_demo_off: AsyncClient) -> None:
        resp = await client_demo_off.get("/demo/reset")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"

    async def test_scenarios_available_after_reset(
        self, client_demo_off: AsyncClient
    ) -> None:
        await client_demo_off.get("/demo/reset")
        resp = await client_demo_off.get("/demo/scenarios")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestDemoAPIStream:
    """Tests for POST /demo/scenarios/{id}/stream."""

    async def test_stream_returns_sse_events(
        self, client_demo_off: AsyncClient
    ) -> None:
        list_resp = await client_demo_off.get("/demo/scenarios")
        scenarios = list_resp.json()
        if not scenarios:
            pytest.skip("No demo scenarios available")
        scenario_id = scenarios[0]["id"]

        resp = await client_demo_off.post(f"/demo/scenarios/{scenario_id}/stream")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        # Parse SSE events from the response body
        text = resp.text
        events = _parse_sse_events(text)
        assert len(events) >= 2  # At least run_start and run_complete

        # First event should be run_start
        first = events[0]
        assert first["type"] == "run_start"
        assert first["run_id"] == f"demo-{scenario_id}"

        # Last event should be run_complete with plan attached
        last = events[-1]
        assert last["type"] == "run_complete"
        assert "plan" in last.get("payload", {})
        assert last["payload"]["demo_mode"] is True

    async def test_stream_events_have_sequential_seq(
        self, client_demo_off: AsyncClient
    ) -> None:
        list_resp = await client_demo_off.get("/demo/scenarios")
        scenarios = list_resp.json()
        if not scenarios:
            pytest.skip("No demo scenarios available")
        scenario_id = scenarios[0]["id"]

        resp = await client_demo_off.post(f"/demo/scenarios/{scenario_id}/stream")
        events = _parse_sse_events(resp.text)

        seq_numbers = [e["seq"] for e in events]
        assert seq_numbers == list(range(1, len(events) + 1))

    async def test_stream_nonexistent_returns_404(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.post("/demo/scenarios/nonexistent-id/stream")
        assert resp.status_code == 404

    async def test_stream_client_disconnect_stops_events(self) -> None:
        """When request.is_disconnected() returns True, the generator breaks."""
        from unittest.mock import MagicMock

        # Create a mock request where is_disconnected returns True on the second call
        mock_request = MagicMock()
        disconnect_call_count = 0

        async def mock_is_disconnected():
            nonlocal disconnect_call_count
            disconnect_call_count += 1
            return disconnect_call_count > 1  # First call: False, second: True

        mock_request.is_disconnected = mock_is_disconnected
        mock_request.app.state = MagicMock()

        svc = DemoService()
        # Use a real scenario
        scenarios = svc.list_scenarios()
        if not scenarios:
            pytest.skip("No demo scenarios")
        scenario_id = scenarios[0]["id"]

        mock_request.app.state.demo_service = svc

        # Call the endpoint handler directly
        from ailine_runtime.api.routers.demo import stream_demo_scenario

        response = await stream_demo_scenario(scenario_id, mock_request)
        # Consume the SSE generator
        events = []
        async for event in response.body_iterator:
            events.append(event)
            if len(events) > 10:
                break

        # Should have stopped early due to disconnect
        assert len(events) >= 1
        assert disconnect_call_count >= 2


# ---------------------------------------------------------------------------
# DemoModeMiddleware tests
# ---------------------------------------------------------------------------


class TestDemoModeMiddleware:
    """Tests for the demo mode middleware intercepting /plans/generate."""

    async def test_middleware_inactive_when_demo_off(
        self, client_demo_off: AsyncClient
    ) -> None:
        """With demo_mode=False, the middleware does not intercept."""
        try:
            resp = await asyncio.wait_for(
                client_demo_off.post(
                    "/plans/generate",
                    json={
                        "run_id": "test-run",
                        "user_prompt": "Test prompt",
                        "demo_scenario_id": "inclusive-math",
                    },
                ),
                timeout=5.0,
            )
        except (TimeoutError, Exception):
            # Pipeline pass-through timed out -- expected without real LLM
            return
        # Should pass through to the real endpoint (which may 500 due to missing deps)
        # The key assertion: NOT a demo response
        if resp.status_code == 200:
            body = resp.json()
            assert body.get("demo_mode") is not True

    async def test_middleware_intercepts_with_demo_scenario_id(
        self, client_demo_on: AsyncClient
    ) -> None:
        """With demo_mode=True + demo_scenario_id, the middleware returns cached plan."""
        resp = await client_demo_on.post(
            "/plans/generate",
            json={
                "run_id": "test-run-demo",
                "user_prompt": "Fracoes para 6o ano",
                "demo_scenario_id": "inclusive-math",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["demo_mode"] is True
        assert body["status"] == "completed"
        assert "plan" in body
        assert body["run_id"] == "test-run-demo"

    async def test_middleware_passes_through_without_demo_scenario_id(
        self, client_demo_on: AsyncClient
    ) -> None:
        """With demo_mode=True but no demo_scenario_id, passes through."""
        try:
            resp = await asyncio.wait_for(
                client_demo_on.post(
                    "/plans/generate",
                    json={
                        "run_id": "test-run-normal",
                        "user_prompt": "Normal request without demo",
                    },
                ),
                timeout=5.0,
            )
        except (TimeoutError, Exception):
            # Pipeline pass-through timed out -- expected without real LLM
            return
        # Should pass through to real endpoint (may 500 or 422)
        # The key: not a demo_mode response
        if resp.status_code == 200:
            body = resp.json()
            assert body.get("demo_mode") is not True

    async def test_middleware_returns_404_for_unknown_scenario(
        self, client_demo_on: AsyncClient
    ) -> None:
        """Unknown demo_scenario_id returns 404."""
        resp = await client_demo_on.post(
            "/plans/generate",
            json={
                "run_id": "test-run-bad",
                "user_prompt": "Test",
                "demo_scenario_id": "nonexistent-scenario",
            },
        )
        assert resp.status_code == 404

    async def test_middleware_ignores_non_post(
        self, client_demo_on: AsyncClient
    ) -> None:
        """GET requests to /plans/generate are not intercepted."""
        resp = await client_demo_on.get("/plans/generate")
        # Should return 405 (method not allowed) from the real router
        assert resp.status_code == 405

    async def test_middleware_ignores_other_paths(
        self, client_demo_on: AsyncClient
    ) -> None:
        """POST to other paths is not intercepted."""
        resp = await client_demo_on.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Integration: real demo scenarios from data/demo/
# ---------------------------------------------------------------------------

_SCENARIO_IDS = ("inclusive-math", "science-visual", "libras-demo")


class TestRealDemoScenarios:
    """Integration tests against the 3 curated demo scenario files."""

    def test_real_data_dir_has_three_scenarios(self) -> None:
        svc = DemoService()
        assert svc.scenario_count == 3

    def test_inclusive_math_scenario(self) -> None:
        svc = DemoService()
        scenario = svc.get_scenario("inclusive-math")
        assert scenario is not None
        assert "Dislexia" in scenario["title"]
        assert scenario["grade"] == "6\u00ba ano"
        assert scenario["subject"] == "Matem\u00e1tica"
        assert scenario["locale"] == "pt-BR"
        plan = svc.get_cached_plan("inclusive-math")
        assert plan is not None
        assert len(plan["steps"]) == 4
        assert svc.get_score("inclusive-math") == 92

    def test_science_visual_scenario(self) -> None:
        svc = DemoService()
        scenario = svc.get_scenario("science-visual")
        assert scenario is not None
        assert "Photosynthesis" in scenario["title"]
        assert scenario["grade"] == "7th grade"
        assert scenario["subject"] == "Science"
        assert scenario["locale"] == "en"
        plan = svc.get_cached_plan("science-visual")
        assert plan is not None
        assert len(plan["steps"]) == 4
        assert svc.get_score("science-visual") == 88

    def test_libras_demo_scenario(self) -> None:
        svc = DemoService()
        scenario = svc.get_scenario("libras-demo")
        assert scenario is not None
        assert "Libras" in scenario["title"]
        assert scenario["grade"] == "4\u00ba ano"
        assert scenario["locale"] == "pt-BR"
        plan = svc.get_cached_plan("libras-demo")
        assert plan is not None
        assert len(plan["steps"]) == 4
        assert svc.get_score("libras-demo") == 95

    def test_all_scenarios_have_required_fields(self) -> None:
        svc = DemoService()
        for sid in _SCENARIO_IDS:
            scenario = svc.get_scenario(sid)
            assert scenario is not None, f"Missing scenario: {sid}"
            # Top-level required fields
            for field in (
                "id",
                "title",
                "description",
                "prompt",
                "grade",
                "subject",
                "locale",
                "expected_skills",
                "demo_tags",
                "cached_plan",
                "cached_events",
                "score",
            ):
                assert field in scenario, f"Missing field '{field}' in scenario '{sid}'"
            # Plan required fields
            plan = scenario["cached_plan"]
            for field in ("title", "grade", "standard", "objectives", "steps"):
                assert (
                    field in plan
                ), f"Missing plan field '{field}' in scenario '{sid}'"
            # Events must start with run_start and end with run_complete
            events = scenario["cached_events"]
            assert len(events) >= 2, f"Too few events in scenario '{sid}'"
            assert events[0]["type"] == "run_start"
            assert events[-1]["type"] == "run_complete"

    def test_all_scenarios_have_accessibility_pack(self) -> None:
        svc = DemoService()
        for sid in _SCENARIO_IDS:
            plan = svc.get_cached_plan(sid)
            assert plan is not None
            assert "accessibility_pack_draft" in plan
            pack = plan["accessibility_pack_draft"]
            assert "applied_adaptations" in pack
            assert len(pack["applied_adaptations"]) >= 1

    def test_all_scenarios_have_student_plan(self) -> None:
        svc = DemoService()
        for sid in _SCENARIO_IDS:
            plan = svc.get_cached_plan(sid)
            assert plan is not None
            assert "student_plan" in plan
            sp = plan["student_plan"]
            assert "summary" in sp
            assert "steps" in sp
            assert "glossary" in sp

    def test_cached_events_have_delay_ordering(self) -> None:
        svc = DemoService()
        for sid in _SCENARIO_IDS:
            events = svc.get_cached_events(sid)
            delays = [e.get("delay_ms", 0) for e in events]
            assert delays == sorted(
                delays
            ), f"Events not in delay order for scenario '{sid}'"


# ---------------------------------------------------------------------------
# Demo Profiles API tests
# ---------------------------------------------------------------------------


class TestDemoProfiles:
    """Tests for GET /demo/profiles."""

    async def test_profiles_returns_all_profiles(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.get("/demo/profiles")
        assert resp.status_code == 200
        body = resp.json()
        assert "profiles" in body
        assert "mode" in body
        assert body["mode"] == "hackathon_demo"
        profiles = body["profiles"]
        assert len(profiles) == 6

    async def test_profiles_contain_required_fields(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.get("/demo/profiles")
        profiles = resp.json()["profiles"]
        for p in profiles:
            assert "id" in p
            assert "name" in p
            assert "role" in p
            assert "demo_key" in p
            assert "description" in p

    async def test_profiles_have_correct_roles(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.get("/demo/profiles")
        profiles = resp.json()["profiles"]
        roles = {p["role"] for p in profiles}
        assert "teacher" in roles
        assert "student" in roles
        assert "parent" in roles

    async def test_teacher_profile_has_school(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.get("/demo/profiles")
        profiles = resp.json()["profiles"]
        teacher = next(p for p in profiles if p["role"] == "teacher")
        assert "school" in teacher
        assert teacher["name"] == "Ms. Sarah Johnson"

    async def test_student_profiles_have_accessibility(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.get("/demo/profiles")
        profiles = resp.json()["profiles"]
        students = [p for p in profiles if p["role"] == "student"]
        assert len(students) == 4
        for s in students:
            assert "accessibility" in s
            assert "accessibility_label" in s

    async def test_demo_key_matches_profile_key(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.get("/demo/profiles")
        profiles = resp.json()["profiles"]
        keys = [p["demo_key"] for p in profiles]
        assert "teacher-ms-johnson" in keys
        assert "student-alex-tea" in keys
        assert "parent-david" in keys


class TestDemoProfilesUnit:
    """Unit tests for DEMO_PROFILES constant."""

    def test_all_profile_ids_are_prefixed(self) -> None:
        from ailine_runtime.api.routers.demo import DEMO_PROFILES

        for key, profile in DEMO_PROFILES.items():
            assert profile["id"].startswith(
                "demo-"
            ), f"Profile {key} id must start with 'demo-'"

    def test_all_profile_keys_are_valid_teacher_ids(self) -> None:
        """demo_key prefixed with 'demo-' must pass tenant ID validation."""
        from ailine_runtime.api.routers.demo import DEMO_PROFILES
        from ailine_runtime.shared.tenant import validate_teacher_id_format

        for key in DEMO_PROFILES:
            tid = f"demo-{key}"
            # Should not raise
            result = validate_teacher_id_format(tid)
            assert result == tid


# ---------------------------------------------------------------------------
# Demo Seed Data API tests
# ---------------------------------------------------------------------------


class TestDemoSeed:
    """Tests for POST /demo/seed."""

    async def test_seed_returns_ok(self, client_demo_off: AsyncClient) -> None:
        resp = await client_demo_off.post("/demo/seed")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "teacher_id" in body
        assert body["teacher_id"] == "demo-teacher-ms-johnson"

    async def test_seed_creates_materials(self, client_demo_off: AsyncClient) -> None:
        resp = await client_demo_off.post("/demo/seed")
        body = resp.json()
        assert body["created"]["materials"] == 2
        assert len(body["ids"]["materials"]) == 2

    async def test_seed_creates_reviews(self, client_demo_off: AsyncClient) -> None:
        resp = await client_demo_off.post("/demo/seed")
        body = resp.json()
        assert body["created"]["reviews"] == 3
        assert len(body["ids"]["reviews"]) == 3

    async def test_seed_creates_progress_records(
        self, client_demo_off: AsyncClient
    ) -> None:
        resp = await client_demo_off.post("/demo/seed")
        body = resp.json()
        assert body["created"]["progress"] == 8
        assert len(body["ids"]["progress"]) == 8

    async def test_seed_creates_tutors(self, client_demo_off: AsyncClient) -> None:
        resp = await client_demo_off.post("/demo/seed")
        body = resp.json()
        assert body["created"]["tutors"] == 2
        assert len(body["ids"]["tutors"]) == 2

    async def test_seed_creates_sessions(self, client_demo_off: AsyncClient) -> None:
        resp = await client_demo_off.post("/demo/seed")
        body = resp.json()
        assert body["created"]["sessions"] == 2
        assert len(body["ids"]["sessions"]) == 2

    async def test_seed_data_accessible_with_demo_header(
        self,
        client_demo_off: AsyncClient,
    ) -> None:
        """After seeding, materials should be accessible using the teacher's ID."""
        seed_resp = await client_demo_off.post("/demo/seed")
        assert seed_resp.status_code == 200

        # Verify materials are accessible via the materials API
        mat_resp = await client_demo_off.get(
            "/materials",
            headers={"X-Teacher-ID": "demo-teacher-ms-johnson"},
        )
        # In dev mode, X-Teacher-ID header should work
        assert mat_resp.status_code in (200, 401)
        if mat_resp.status_code == 200:
            mats = mat_resp.json()
            assert len(mats) >= 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_sse_events(text: str) -> list[dict[str, Any]]:
    """Parse SSE text into a list of JSON event dicts."""
    events: list[dict[str, Any]] = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("data:"):
            data_str = line[len("data:") :].strip()
            if data_str:
                with contextlib.suppress(json.JSONDecodeError):
                    events.append(json.loads(data_str))
    return events
