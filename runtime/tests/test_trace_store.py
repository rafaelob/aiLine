"""Tests for the in-memory TraceStore."""

from __future__ import annotations

import pytest

from ailine_runtime.domain.entities.trace import NodeTrace, RouteRationale
from ailine_runtime.shared.trace_store import TraceStore, get_trace_store, reset_trace_store


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset singleton before each test."""
    reset_trace_store()
    yield
    reset_trace_store()


class TestTraceStore:
    """TraceStore stores and retrieves run traces."""

    @pytest.mark.asyncio
    async def test_get_or_create_new(self) -> None:
        store = TraceStore()
        trace = await store.get_or_create("run-1")
        assert trace.run_id == "run-1"
        assert trace.status == "running"
        assert trace.nodes == []

    @pytest.mark.asyncio
    async def test_get_or_create_existing(self) -> None:
        store = TraceStore()
        t1 = await store.get_or_create("run-1")
        t2 = await store.get_or_create("run-1")
        assert t1 is t2

    @pytest.mark.asyncio
    async def test_get_nonexistent(self) -> None:
        store = TraceStore()
        result = await store.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_append_node(self) -> None:
        store = TraceStore()
        node = NodeTrace(node="planner", status="success", time_ms=150.0)
        await store.append_node("run-1", node)
        trace = await store.get("run-1")
        assert trace is not None
        assert len(trace.nodes) == 1
        assert trace.nodes[0].node == "planner"
        assert trace.nodes[0].time_ms == 150.0

    @pytest.mark.asyncio
    async def test_append_multiple_nodes(self) -> None:
        store = TraceStore()
        await store.append_node("run-1", NodeTrace(node="planner", status="success", time_ms=100.0))
        await store.append_node("run-1", NodeTrace(node="validate", status="success", time_ms=50.0, quality_score=85))
        await store.append_node("run-1", NodeTrace(node="executor", status="success", time_ms=200.0))
        trace = await store.get("run-1")
        assert trace is not None
        assert len(trace.nodes) == 3
        assert [n.node for n in trace.nodes] == ["planner", "validate", "executor"]

    @pytest.mark.asyncio
    async def test_update_run(self) -> None:
        store = TraceStore()
        await store.get_or_create("run-1")
        await store.update_run("run-1", status="completed", total_time_ms=500.0, final_score=87)
        trace = await store.get("run-1")
        assert trace is not None
        assert trace.status == "completed"
        assert trace.total_time_ms == 500.0
        assert trace.final_score == 87

    @pytest.mark.asyncio
    async def test_list_recent(self) -> None:
        store = TraceStore()
        await store.get_or_create("run-1")
        await store.get_or_create("run-2")
        await store.get_or_create("run-3")
        recent = await store.list_recent(limit=2)
        assert len(recent) == 2

    @pytest.mark.asyncio
    async def test_capacity_eviction(self) -> None:
        store = TraceStore(max_entries=3)
        await store.get_or_create("run-1")
        await store.get_or_create("run-2")
        await store.get_or_create("run-3")
        await store.get_or_create("run-4")  # should evict run-1
        assert await store.get("run-1") is None
        assert await store.get("run-4") is not None

    @pytest.mark.asyncio
    async def test_ttl_eviction(self) -> None:
        store = TraceStore(ttl_seconds=0)  # Immediate expiry
        await store.get_or_create("run-1")
        # Force eviction by accessing
        result = await store.get("run-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_node_with_route_rationale(self) -> None:
        store = TraceStore()
        rationale = RouteRationale(
            task_type="planner",
            weighted_scores={"token": 0.25, "structured": 0.25},
            composite_score=0.75,
            tier="primary",
            model_selected="claude-opus-4-6",
            reason="SmartRouter selected primary tier",
        )
        node = NodeTrace(
            node="planner",
            status="success",
            time_ms=100.0,
            route_rationale=rationale,
        )
        await store.append_node("run-1", node)
        trace = await store.get("run-1")
        assert trace is not None
        assert trace.nodes[0].route_rationale is not None
        assert trace.nodes[0].route_rationale.tier == "primary"


class TestSingleton:
    """get_trace_store() returns a singleton."""

    def test_singleton(self) -> None:
        s1 = get_trace_store()
        s2 = get_trace_store()
        assert s1 is s2
