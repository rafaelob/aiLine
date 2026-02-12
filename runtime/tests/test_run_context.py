"""Tests for RunContext terminal SSE guarantee (ADR-055)."""

import asyncio

import pytest

from ailine_runtime.api.streaming.events import SSEEventEmitter
from ailine_runtime.api.streaming.replay import InMemoryReplayStore, ReplayConfig
from ailine_runtime.api.streaming.run_context import RunContext


@pytest.fixture()
def replay_store():
    return InMemoryReplayStore(ReplayConfig(keep_last=100))


@pytest.fixture()
def emitter():
    return SSEEventEmitter("test-run-001")


class TestRunContext:
    @pytest.mark.asyncio
    async def test_normal_exit_emits_completed(self, emitter, replay_store):
        queue: asyncio.Queue = asyncio.Queue()

        async with RunContext("test-run-001", emitter, queue, replay_store):
            pass  # Normal exit

        # Collect all events from queue
        events = []
        while not queue.empty():
            item = queue.get_nowait()
            events.append(item)

        # Should have run.started and run.completed
        assert len(events) == 2
        import json

        first = json.loads(events[0]["data"])
        last = json.loads(events[1]["data"])
        assert first["type"] == "run.started"
        assert last["type"] == "run.completed"

    @pytest.mark.asyncio
    async def test_exception_emits_failed(self, emitter, replay_store):
        queue: asyncio.Queue = asyncio.Queue()

        with pytest.raises(ValueError, match="test error"):
            async with RunContext("test-run-001", emitter, queue, replay_store):
                raise ValueError("test error")

        events = []
        while not queue.empty():
            events.append(queue.get_nowait())

        import json

        first = json.loads(events[0]["data"])
        last = json.loads(events[1]["data"])
        assert first["type"] == "run.started"
        assert last["type"] == "run.failed"
        assert "ValueError" in last["payload"]["error"]

    @pytest.mark.asyncio
    async def test_terminal_event_emitted_exactly_once(self, emitter, replay_store):
        queue: asyncio.Queue = asyncio.Queue()

        async with RunContext("test-run-001", emitter, queue, replay_store) as ctx:
            # Manually try to finalize - should be ignored since __aexit__ will finalize
            await ctx._finalize_ok()

        events = []
        while not queue.empty():
            events.append(queue.get_nowait())

        import json

        # Should have exactly: run.started, run.completed (from manual), no duplicate from __aexit__
        types = [json.loads(e["data"])["type"] for e in events]
        assert types.count("run.completed") == 1
        assert types.count("run.started") == 1

    @pytest.mark.asyncio
    async def test_replay_store_receives_events(self, emitter, replay_store):
        queue: asyncio.Queue = asyncio.Queue()

        async with RunContext("test-run-001", emitter, queue, replay_store) as ctx:
            await ctx.emit_stage_start("planner")
            await ctx.emit_stage_complete("planner")

        stored = await replay_store.replay("test-run-001")
        # run.started + stage.started + stage.completed + run.completed = 4
        assert len(stored) == 4

    @pytest.mark.asyncio
    async def test_terminal_marker_set(self, emitter, replay_store):
        queue: asyncio.Queue = asyncio.Queue()

        async with RunContext("test-run-001", emitter, queue, replay_store):
            pass

        assert await replay_store.is_terminal("test-run-001") is True

    @pytest.mark.asyncio
    async def test_emit_stage_events(self, emitter, replay_store):
        queue: asyncio.Queue = asyncio.Queue()

        async with RunContext("test-run-001", emitter, queue, replay_store) as ctx:
            await ctx.emit_stage_start("planner", {"detail": "starting"})
            await ctx.emit_stage_failed("planner", "timeout")

        events = []
        while not queue.empty():
            events.append(queue.get_nowait())

        import json

        types = [json.loads(e["data"])["type"] for e in events]
        assert "stage.started" in types
        assert "stage.failed" in types

    @pytest.mark.asyncio
    async def test_callable_sink(self, emitter, replay_store):
        collected = []

        def sink(event):
            collected.append(event)

        async with RunContext("test-run-001", emitter, sink, replay_store):
            pass

        assert len(collected) == 2  # run.started + run.completed

    @pytest.mark.asyncio
    async def test_seq_monotonic(self, emitter, replay_store):
        queue: asyncio.Queue = asyncio.Queue()

        async with RunContext("test-run-001", emitter, queue, replay_store) as ctx:
            for i in range(5):
                await ctx.emit_stage_start(f"stage-{i}")

        events = []
        while not queue.empty():
            events.append(queue.get_nowait())

        import json

        seqs = [json.loads(e["data"])["seq"] for e in events]
        assert seqs == sorted(seqs)
        assert len(set(seqs)) == len(seqs)  # All unique

    @pytest.mark.asyncio
    async def test_run_id_property(self, emitter, replay_store):
        """RunContext.run_id property returns the run_id passed at construction."""
        queue: asyncio.Queue = asyncio.Queue()

        async with RunContext("test-run-001", emitter, queue, replay_store) as ctx:
            assert ctx.run_id == "test-run-001"

    @pytest.mark.asyncio
    async def test_emitter_property(self, emitter, replay_store):
        """RunContext.emitter property returns the SSEEventEmitter passed at construction."""
        queue: asyncio.Queue = asyncio.Queue()

        async with RunContext("test-run-001", emitter, queue, replay_store) as ctx:
            assert ctx.emitter is emitter

    @pytest.mark.asyncio
    async def test_finalize_error_skipped_when_already_finalized(self, emitter, replay_store):
        """_finalize_error is a no-op when _finalized is already True (line 107 coverage)."""
        queue: asyncio.Queue = asyncio.Queue()

        async with RunContext("test-run-001", emitter, queue, replay_store) as ctx:
            # Manually finalize with success first
            await ctx._finalize_ok()
            assert ctx._finalized is True
            # Now call _finalize_error -- should be a no-op
            await ctx._finalize_error(RuntimeError("should be ignored"))

        events = []
        while not queue.empty():
            events.append(queue.get_nowait())

        import json

        types = [json.loads(e["data"])["type"] for e in events]
        # Should have: run.started, run.completed (from manual _finalize_ok)
        # NO run.failed should appear
        assert "run.failed" not in types
        assert types.count("run.completed") == 1
