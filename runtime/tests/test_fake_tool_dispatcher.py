"""Tests for FINDING-17: FakeToolDispatcher for executor tool testing."""

from __future__ import annotations

import pytest

from ailine_runtime.adapters.tools.fake_dispatcher import FakeToolDispatcher, ToolCall


class TestFakeToolDispatcher:
    @pytest.mark.asyncio
    async def test_dispatch_records_call(self):
        dispatcher = FakeToolDispatcher()
        await dispatcher.dispatch("rag_search", {"query": "fractions"})
        assert dispatcher.call_count == 1
        assert dispatcher.calls[0].tool_name == "rag_search"
        assert dispatcher.calls[0].args == {"query": "fractions"}

    @pytest.mark.asyncio
    async def test_dispatch_returns_configured_response(self):
        dispatcher = FakeToolDispatcher(responses={"rag_search": {"chunks": ["chunk1"], "note": "fake"}})
        result = await dispatcher.dispatch("rag_search", {"query": "test"})
        assert result == {"chunks": ["chunk1"], "note": "fake"}

    @pytest.mark.asyncio
    async def test_dispatch_returns_default_for_unknown_tool(self):
        dispatcher = FakeToolDispatcher()
        result = await dispatcher.dispatch("unknown_tool", {"arg": "val"})
        assert result == {"status": "ok", "tool_name": "unknown_tool"}

    @pytest.mark.asyncio
    async def test_multiple_dispatches(self):
        dispatcher = FakeToolDispatcher(
            responses={
                "rag_search": {"chunks": []},
                "save_plan": {"plan_id": "test-123"},
            }
        )
        r1 = await dispatcher.dispatch("rag_search", {"query": "q"})
        r2 = await dispatcher.dispatch("save_plan", {"plan_json": {}})
        assert r1 == {"chunks": []}
        assert r2 == {"plan_id": "test-123"}
        assert dispatcher.call_count == 2

    @pytest.mark.asyncio
    async def test_calls_for_filters_by_tool_name(self):
        dispatcher = FakeToolDispatcher()
        await dispatcher.dispatch("rag_search", {"query": "a"})
        await dispatcher.dispatch("save_plan", {"plan_json": {}})
        await dispatcher.dispatch("rag_search", {"query": "b"})

        rag_calls = dispatcher.calls_for("rag_search")
        assert len(rag_calls) == 2
        save_calls = dispatcher.calls_for("save_plan")
        assert len(save_calls) == 1

    @pytest.mark.asyncio
    async def test_reset_clears_calls(self):
        dispatcher = FakeToolDispatcher()
        await dispatcher.dispatch("rag_search", {"query": "test"})
        assert dispatcher.call_count == 1
        dispatcher.reset()
        assert dispatcher.call_count == 0
        assert dispatcher.calls == []

    def test_tool_call_dataclass(self):
        tc = ToolCall(tool_name="test_tool", args={"key": "value"})
        assert tc.tool_name == "test_tool"
        assert tc.args == {"key": "value"}
