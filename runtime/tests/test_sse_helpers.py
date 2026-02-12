"""Tests for SSE helpers (api.streaming.sse)."""

from __future__ import annotations

import json

import pytest

from ailine_runtime.api.streaming.sse import format_sse_event, heartbeat_generator


class TestFormatSSEEvent:
    def test_basic_event(self):
        result = format_sse_event("progress", {"step": 1, "status": "ok"})
        assert result.startswith("event: progress\n")
        assert "data: " in result
        assert result.endswith("\n\n")
        data_line = result.split("\n")[1]
        payload = json.loads(data_line.removeprefix("data: "))
        assert payload == {"step": 1, "status": "ok"}

    def test_unicode_data(self):
        result = format_sse_event("msg", {"text": "Educacao inclusiva"})
        assert "Educacao inclusiva" in result


class TestHeartbeatGenerator:
    @pytest.mark.asyncio
    async def test_generates_heartbeat_event(self):
        gen = heartbeat_generator(interval=0.01)
        event = await gen.__anext__()
        assert "heartbeat" in event
        assert "alive" in event
        await gen.aclose()

    @pytest.mark.asyncio
    async def test_multiple_heartbeats(self):
        gen = heartbeat_generator(interval=0.01)
        events = []
        for _ in range(3):
            events.append(await gen.__anext__())
        assert len(events) == 3
        await gen.aclose()
