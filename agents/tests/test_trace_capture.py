"""Tests for trace capture helpers."""

from __future__ import annotations

import pytest

from ailine_agents.workflows._trace_capture import build_route_rationale, capture_node_trace


class TestBuildRouteRationale:
    """build_route_rationale produces valid rationale dicts."""

    def test_without_selector(self) -> None:
        r = build_route_rationale("planner", "claude-opus-4-6", model_selector=None)
        assert r["task_type"] == "planner"
        assert r["model_selected"] == "claude-opus-4-6"
        assert r["tier"] == "primary"
        assert r["weighted_scores"] == {}

    def test_with_selector(self) -> None:
        # Simulate a model selector (any truthy object)
        r = build_route_rationale("executor", "gemini-pro", model_selector=object())
        assert r["task_type"] == "executor"
        assert r["model_selected"] == "gemini-pro"
        assert r["weighted_scores"]["token"] == 0.25
        assert "SmartRouter" in r["reason"]

    def test_custom_tier(self) -> None:
        r = build_route_rationale("planner", "haiku", model_selector=None, tier="cheap")
        assert r["tier"] == "cheap"


class TestCaptureNodeTrace:
    """capture_node_trace gracefully handles missing runtime."""

    @pytest.mark.asyncio
    async def test_capture_success(self) -> None:
        """Should not raise even when runtime is available."""
        # This test exercises the code path; trace store state verified in runtime tests
        await capture_node_trace(
            run_id="test-run",
            node_name="planner",
            status="success",
            time_ms=100.0,
            inputs_summary={"prompt_length": 500},
            outputs_summary={"draft_keys": ["title", "steps"]},
        )

    @pytest.mark.asyncio
    async def test_capture_with_error(self) -> None:
        await capture_node_trace(
            run_id="test-run",
            node_name="planner",
            status="failed",
            time_ms=50.0,
            error="LLM timeout",
        )

    @pytest.mark.asyncio
    async def test_capture_with_rationale(self) -> None:
        rationale = build_route_rationale("planner", "claude-opus-4-6", None)
        await capture_node_trace(
            run_id="test-run",
            node_name="planner",
            status="success",
            time_ms=100.0,
            route_rationale=rationale,
        )
