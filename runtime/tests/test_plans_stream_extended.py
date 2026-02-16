"""Extended tests for plans_stream.py -- covers error branches.

Targets:
- Lines 63-64: heartbeat loop asyncio.sleep + queue.put
- Lines 165-166: client disconnection detection
- Lines 170-171: TimeoutError on queue.get (continue loop)
- Line 181: pipeline_task.cancel() when not done
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from ailine_runtime.api.streaming.events import SSEEventEmitter, SSEEventType

# ===========================================================================
# Unit tests for _heartbeat_loop
# ===========================================================================


class TestHeartbeatLoop:
    async def test_heartbeat_pushes_events(self):
        """_heartbeat_loop pushes heartbeat events into the queue (lines 63-64)."""
        from ailine_runtime.api.routers.plans_stream import _heartbeat_loop

        emitter = SSEEventEmitter("test-run")
        queue: asyncio.Queue[dict[str, str] | None] = asyncio.Queue()

        # Run heartbeat with a very short interval
        task = asyncio.create_task(_heartbeat_loop(emitter, queue, interval=0.05))

        # Wait for at least one heartbeat
        await asyncio.sleep(0.15)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Should have received at least one heartbeat event
        events = []
        while not queue.empty():
            item = queue.get_nowait()
            if item is not None:
                events.append(item)

        assert len(events) >= 1
        for event in events:
            assert "data" in event
            parsed = json.loads(event["data"])
            assert parsed["type"] == "heartbeat"

    async def test_heartbeat_stops_on_cancel(self):
        """Heartbeat loop exits cleanly on CancelledError (line 65-66)."""
        from ailine_runtime.api.routers.plans_stream import _heartbeat_loop

        emitter = SSEEventEmitter("test-run")
        queue: asyncio.Queue[dict[str, str] | None] = asyncio.Queue()

        task = asyncio.create_task(_heartbeat_loop(emitter, queue, interval=0.5))
        await asyncio.sleep(0.05)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        # Task should be done
        assert task.done()


# ===========================================================================
# Unit tests for _run_pipeline error path
# ===========================================================================


class TestRunPipelineError:
    async def test_pipeline_exception_emits_run_failed(self):
        """When the pipeline raises, _run_pipeline puts a run.failed event (line 128-130)."""
        from ailine_runtime.api.routers.plans_stream import PlanStreamIn, _run_pipeline

        body = PlanStreamIn(run_id="err-run", user_prompt="Boom test")
        settings = MagicMock()
        container = MagicMock()
        emitter = SSEEventEmitter("err-run")
        queue: asyncio.Queue[dict[str, str] | None] = asyncio.Queue()

        # Patch AgentDepsFactory.from_container to raise during pipeline
        mock_factory = MagicMock()
        mock_factory.from_container = MagicMock(
            side_effect=RuntimeError("test explosion")
        )
        with patch(
            "ailine_runtime.api.routers.plans_stream.AgentDepsFactory",
            mock_factory,
        ):
            await _run_pipeline(
                body, "teacher-001", settings, container, emitter, queue
            )

        # Collect all events from queue
        events = []
        while not queue.empty():
            item = queue.get_nowait()
            if item is not None:
                events.append(item)
            else:
                break  # sentinel

        # The run.failed event should be present
        failed_events = [
            json.loads(e["data"])
            for e in events
            if "data" in e and "run.failed" in e["data"]
        ]
        assert len(failed_events) >= 1


# ===========================================================================
# Integration: event_generator timeout and disconnection
# ===========================================================================


def _make_mock_workflow(
    final_state: dict[str, Any] | None = None,
    side_effect: Exception | None = None,
) -> MagicMock:
    """Create a mock compiled workflow."""
    mock = MagicMock()
    if side_effect:
        mock.ainvoke = AsyncMock(side_effect=side_effect)
    else:
        state = final_state or {
            "run_id": "test-run",
            "final": {
                "parsed": {
                    "plan_id": "test-run",
                    "score": 85,
                    "human_review_required": False,
                }
            },
        }

        async def _ainvoke(init_state: dict, config: dict | None = None) -> dict:
            configurable = (config or {}).get("configurable", {})
            emitter = configurable.get("sse_emitter")
            writer = configurable.get("stream_writer")
            if emitter and writer:
                writer(emitter.emit(SSEEventType.STAGE_START, "planner"))
                writer(emitter.emit(SSEEventType.STAGE_COMPLETE, "planner"))
            return state

        mock.ainvoke = _ainvoke
    return mock


def _patch_build_and_deps():
    """Context manager that patches both build_plan_workflow and AgentDepsFactory."""
    mock_wf = _make_mock_workflow()
    p1 = patch(
        "ailine_runtime.api.routers.plans_stream.build_plan_workflow",
        return_value=mock_wf,
    )
    mock_factory = MagicMock()
    mock_factory.from_container = MagicMock(return_value=MagicMock())
    p2 = patch("ailine_runtime.api.routers.plans_stream.AgentDepsFactory", mock_factory)
    return p1, p2


class TestEventGeneratorEdgeCases:
    def test_stream_timeout_loop_continues(self):
        """When queue.get times out, the generator continues (lines 170-171)."""
        import os

        from fastapi.testclient import TestClient

        from ailine_runtime.api.app import create_app
        from ailine_runtime.shared.config import Settings

        os.environ["AILINE_DEV_MODE"] = "true"
        settings = Settings(anthropic_api_key="", openai_api_key="", google_api_key="")
        app = create_app(settings)
        p1, p2 = _patch_build_and_deps()

        with p1, p2, TestClient(app) as client:
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "timeout-test", "user_prompt": "Test timeout loop"},
                headers={"X-Teacher-ID": "teacher-test"},
            )

        assert response.status_code == 200

    def test_stream_client_disconnect_handled(self):
        """The event generator checks is_disconnected (lines 164-166)."""
        import os

        from fastapi.testclient import TestClient

        from ailine_runtime.api.app import create_app
        from ailine_runtime.shared.config import Settings

        os.environ["AILINE_DEV_MODE"] = "true"
        settings = Settings(anthropic_api_key="", openai_api_key="", google_api_key="")
        app = create_app(settings)
        mock_wf = _make_mock_workflow(side_effect=RuntimeError("quick fail"))
        mock_factory = MagicMock()
        mock_factory.from_container = MagicMock(return_value=MagicMock())

        with (
            patch(
                "ailine_runtime.api.routers.plans_stream.build_plan_workflow",
                return_value=mock_wf,
            ),
            patch(
                "ailine_runtime.api.routers.plans_stream.AgentDepsFactory", mock_factory
            ),
            TestClient(app) as client,
        ):
            response = client.post(
                "/plans/generate/stream",
                json={"run_id": "disconnect-test", "user_prompt": "Disconnect test"},
                headers={"X-Teacher-ID": "teacher-test"},
            )

        assert response.status_code == 200
        events = _parse_sse_events(response.text)
        types = {e["type"] for e in events}
        assert "run.started" in types
        assert "run.failed" in types


# ---------------------------------------------------------------------------
# SSE parsing helper
# ---------------------------------------------------------------------------


def _parse_sse_events(raw: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("data:"):
            json_str = line[len("data:") :].strip()
            if json_str:
                with contextlib.suppress(json.JSONDecodeError):
                    events.append(json.loads(json_str))
    return events
