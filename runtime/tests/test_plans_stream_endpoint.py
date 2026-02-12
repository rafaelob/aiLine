"""Integration tests for the SSE streaming endpoint POST /plans/generate/stream.

Mocks the Pydantic AI agent workflow (build_plan_workflow) so no external
API calls are made (ADR-051). Tests verify SSE event stream correctness.
"""

from __future__ import annotations

import contextlib
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from ailine_runtime.api.app import create_app
from ailine_runtime.api.streaming.events import SSEEventType
from ailine_runtime.shared.config import Settings

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _test_settings() -> Settings:
    """Settings configured with no real API keys."""
    return Settings(
        anthropic_api_key="",
        openai_api_key="",
        google_api_key="",
    )


_GOOD_FINAL_STATE = {
    "run_id": "test-run",
    "user_prompt": "Plano de teste",
    "draft": {"title": "Plano"},
    "validation": {"score": 85, "status": "accept"},
    "final": {"parsed": {"plan_id": "test-run", "score": 85, "human_review_required": False}},
    "refine_iter": 0,
}


def _make_mock_workflow(
    final_state: dict[str, Any] | None = None,
    side_effect: Exception | None = None,
) -> MagicMock:
    """Create a mock compiled workflow that simulates ainvoke()."""
    mock = MagicMock()
    if side_effect:
        mock.ainvoke = AsyncMock(side_effect=side_effect)
    else:
        state = final_state or _GOOD_FINAL_STATE

        async def _ainvoke(init_state: dict, config: dict | None = None) -> dict:
            # Emit SSE events if emitter is provided (simulates the real workflow)
            configurable = (config or {}).get("configurable", {})
            emitter = configurable.get("sse_emitter")
            writer = configurable.get("stream_writer")
            if emitter and writer:
                writer(emitter.emit(SSEEventType.STAGE_START, "planner"))
                writer(emitter.emit(SSEEventType.STAGE_COMPLETE, "planner"))
                writer(emitter.emit(SSEEventType.STAGE_START, "validate"))
                writer(emitter.emit(SSEEventType.QUALITY_SCORED, "validate", {"score": 85, "status": "accept"}))
                writer(emitter.emit(SSEEventType.QUALITY_DECISION, "validate", {"decision": "accept", "score": 85}))
                writer(emitter.emit(SSEEventType.STAGE_COMPLETE, "validate"))
                writer(emitter.emit(SSEEventType.STAGE_START, "executor"))
                writer(emitter.emit(SSEEventType.STAGE_COMPLETE, "executor"))
            return state

        mock.ainvoke = _ainvoke
    return mock


def _patch_build_workflow(mock_workflow: MagicMock):
    """Patch build_plan_workflow in the plans_stream router."""
    return patch(
        "ailine_runtime.api.routers.plans_stream.build_plan_workflow",
        return_value=mock_workflow,
    )


def _patch_agent_deps_factory():
    """Patch AgentDepsFactory.from_container to avoid real container."""
    mock_factory = MagicMock()
    mock_factory.from_container = MagicMock(return_value=MagicMock())
    return patch(
        "ailine_runtime.api.routers.plans_stream.AgentDepsFactory",
        mock_factory,
    )


# ---------------------------------------------------------------------------
# Tests: Streaming endpoint
# ---------------------------------------------------------------------------


class TestPlansStreamEndpoint:
    """Verify the /plans/generate/stream SSE endpoint."""

    def _make_app(self) -> Any:
        return create_app(_test_settings())

    def test_endpoint_returns_sse_content_type(self) -> None:
        """Response should have text/event-stream content type."""
        app = self._make_app()
        mock_wf = _make_mock_workflow()

        with _patch_build_workflow(mock_wf), _patch_agent_deps_factory(), TestClient(app) as client:
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "test-001", "user_prompt": "Crie um plano de matematica"},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

    def test_stream_contains_run_started_and_completed(self) -> None:
        """SSE stream should always include run.started and run.completed."""
        app = self._make_app()
        mock_wf = _make_mock_workflow()

        with _patch_build_workflow(mock_wf), _patch_agent_deps_factory(), TestClient(app) as client:
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "test-002", "user_prompt": "Plano de ciencias"},
            )

        events = _parse_sse_events(response.text)
        types = {e["type"] for e in events}
        assert "run.started" in types
        assert "run.completed" in types

    def test_stream_events_have_correct_envelope(self) -> None:
        """Every SSE event should have the required envelope fields."""
        app = self._make_app()
        mock_wf = _make_mock_workflow()

        with _patch_build_workflow(mock_wf), _patch_agent_deps_factory(), TestClient(app) as client:
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "test-003", "user_prompt": "Plano de historia"},
            )

        events = _parse_sse_events(response.text)
        assert len(events) > 0

        for event in events:
            assert "run_id" in event, f"Missing run_id in event: {event}"
            assert "seq" in event, f"Missing seq in event: {event}"
            assert "ts" in event, f"Missing ts in event: {event}"
            assert "type" in event, f"Missing type in event: {event}"
            assert "stage" in event, f"Missing stage in event: {event}"
            assert "payload" in event, f"Missing payload in event: {event}"

    def test_stream_events_monotonic_sequence(self) -> None:
        """Event sequence numbers should be monotonically increasing."""
        app = self._make_app()
        mock_wf = _make_mock_workflow()

        with _patch_build_workflow(mock_wf), _patch_agent_deps_factory(), TestClient(app) as client:
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "test-004", "user_prompt": "Plano de portugues"},
            )

        events = _parse_sse_events(response.text)
        seqs = [e["seq"] for e in events]
        assert seqs == sorted(seqs), f"Sequences not monotonic: {seqs}"
        assert len(set(seqs)) == len(seqs), f"Duplicate sequences: {seqs}"

    def test_stream_run_id_matches_request(self) -> None:
        """All events should carry the same run_id as the request."""
        app = self._make_app()
        mock_wf = _make_mock_workflow()

        with _patch_build_workflow(mock_wf), _patch_agent_deps_factory(), TestClient(app) as client:
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "my-unique-run", "user_prompt": "Test run id"},
            )

        events = _parse_sse_events(response.text)
        for event in events:
            assert event["run_id"] == "my-unique-run"

    def test_stream_error_produces_run_failed(self) -> None:
        """If the pipeline raises, stream should contain run.failed."""
        app = self._make_app()
        mock_wf = _make_mock_workflow(side_effect=RuntimeError("Boom"))

        with _patch_build_workflow(mock_wf), _patch_agent_deps_factory(), TestClient(app) as client:
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "error-run", "user_prompt": "This will fail"},
            )

        events = _parse_sse_events(response.text)
        types = {e["type"] for e in events}
        assert "run.started" in types
        assert "run.failed" in types

        failed_events = [e for e in events if e["type"] == "run.failed"]
        assert len(failed_events) == 1
        assert "Boom" in failed_events[0]["payload"].get("error", "")

    def test_validation_required_fields(self) -> None:
        """Missing required fields should return 422."""
        app = self._make_app()

        with TestClient(app) as client:
            # Missing user_prompt
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "no-prompt"},
            )
            assert response.status_code == 422

            # Missing run_id
            response = client.post(
                "/plans/generate/stream",
                json={"user_prompt": "hello"},
            )
            assert response.status_code == 422

    def test_sse_reverse_proxy_headers(self) -> None:
        """SSE response should include headers for reverse proxy compatibility."""
        app = self._make_app()
        mock_wf = _make_mock_workflow()

        with _patch_build_workflow(mock_wf), _patch_agent_deps_factory(), TestClient(app) as client:
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "headers-run", "user_prompt": "Test headers"},
            )

        assert response.status_code == 200
        assert response.headers.get("x-accel-buffering") == "no"
        assert response.headers.get("cache-control") == "no-cache, no-store"
        assert response.headers.get("connection") == "keep-alive"

    def test_quality_scored_event_in_stream(self) -> None:
        """Stream should include quality.scored event with score."""
        app = self._make_app()
        mock_wf = _make_mock_workflow()

        with _patch_build_workflow(mock_wf), _patch_agent_deps_factory(), TestClient(app) as client:
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "quality-run", "user_prompt": "Test quality"},
            )

        events = _parse_sse_events(response.text)
        scored = [e for e in events if e["type"] == "quality.scored"]
        assert len(scored) >= 1
        assert "score" in scored[0]["payload"]


# ---------------------------------------------------------------------------
# SSE parsing helper
# ---------------------------------------------------------------------------


def _parse_sse_events(raw: str) -> list[dict[str, Any]]:
    """Parse raw SSE text into a list of JSON event dicts."""
    events: list[dict[str, Any]] = []
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("data:"):
            json_str = line[len("data:"):].strip()
            if json_str:
                with contextlib.suppress(json.JSONDecodeError):
                    events.append(json.loads(json_str))
    return events
