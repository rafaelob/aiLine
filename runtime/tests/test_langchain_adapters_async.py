"""Tests for tools/adapters_langchain.py -- covers the async _run function (lines 17-19).

Lines 17-19: the closure that instantiates args_model, calls handler, and returns JSON.
"""

from __future__ import annotations

import importlib
import json
import sys
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from ailine_runtime.tools.registry import ToolDef

# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


class SampleArgs(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(5, description="Max results")


async def sample_handler(args: SampleArgs) -> dict:
    return {"results": [args.query], "count": args.limit}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_registry() -> list[ToolDef]:
    return [
        ToolDef(
            name="sample_tool",
            description="A sample tool for testing",
            args_model=SampleArgs,
            handler=sample_handler,
        )
    ]


# ===========================================================================
# Tests
# ===========================================================================


class TestLangchainAdaptersAsyncRun:
    """Test that the async _run function (lines 17-19) works correctly."""

    async def test_run_function_calls_handler_and_returns_json(self, sample_registry):
        """The coroutine passed to StructuredTool.from_function should:
        1. Parse kwargs into args_model
        2. Call the handler
        3. Return JSON string
        """
        # We need to capture the coroutine that from_function receives
        captured_coroutines = []

        mock_structured_tool = MagicMock()

        def capture_from_function(**kwargs):
            captured_coroutines.append(kwargs.get("coroutine"))
            return MagicMock()

        mock_structured_tool.from_function = capture_from_function
        mock_lc_tools = MagicMock()
        mock_lc_tools.StructuredTool = mock_structured_tool

        with patch.dict(
            sys.modules,
            {"langchain_core": MagicMock(), "langchain_core.tools": mock_lc_tools},
        ):
            import ailine_runtime.tools.adapters_langchain as lc_mod

            importlib.reload(lc_mod)
            lc_mod.to_langchain_tools(sample_registry)

        assert len(captured_coroutines) == 1
        run_fn = captured_coroutines[0]
        assert run_fn is not None

        # Call the captured async _run function (lines 17-19)
        result_str = await run_fn(query="test search", limit=3)

        result = json.loads(result_str)
        assert result == {"results": ["test search"], "count": 3}

    async def test_run_function_with_defaults(self, sample_registry):
        """Test _run with only required args, relying on model defaults."""
        captured_coroutines = []

        mock_structured_tool = MagicMock()

        def capture_from_function(**kwargs):
            captured_coroutines.append(kwargs.get("coroutine"))
            return MagicMock()

        mock_structured_tool.from_function = capture_from_function
        mock_lc_tools = MagicMock()
        mock_lc_tools.StructuredTool = mock_structured_tool

        with patch.dict(
            sys.modules,
            {"langchain_core": MagicMock(), "langchain_core.tools": mock_lc_tools},
        ):
            import ailine_runtime.tools.adapters_langchain as lc_mod

            importlib.reload(lc_mod)
            lc_mod.to_langchain_tools(sample_registry)

        run_fn = captured_coroutines[0]
        result_str = await run_fn(query="hello")
        result = json.loads(result_str)
        assert result["results"] == ["hello"]
        assert result["count"] == 5  # default value

    async def test_multiple_tools_each_get_own_run_fn(self):
        """Each tool in the registry should get its own closure."""

        class ArgsA(BaseModel):
            x: str = "a"

        class ArgsB(BaseModel):
            y: int = 42

        async def handler_a(args: ArgsA) -> dict:
            return {"tool": "a", "x": args.x}

        async def handler_b(args: ArgsB) -> dict:
            return {"tool": "b", "y": args.y}

        registry = [
            ToolDef(
                name="tool_a", description="Tool A", args_model=ArgsA, handler=handler_a
            ),
            ToolDef(
                name="tool_b", description="Tool B", args_model=ArgsB, handler=handler_b
            ),
        ]

        captured_coroutines = []

        mock_structured_tool = MagicMock()

        def capture_from_function(**kwargs):
            captured_coroutines.append(kwargs.get("coroutine"))
            return MagicMock()

        mock_structured_tool.from_function = capture_from_function
        mock_lc_tools = MagicMock()
        mock_lc_tools.StructuredTool = mock_structured_tool

        with patch.dict(
            sys.modules,
            {"langchain_core": MagicMock(), "langchain_core.tools": mock_lc_tools},
        ):
            import ailine_runtime.tools.adapters_langchain as lc_mod

            importlib.reload(lc_mod)
            lc_mod.to_langchain_tools(registry)

        assert len(captured_coroutines) == 2

        result_a = json.loads(await captured_coroutines[0](x="hello"))
        assert result_a["tool"] == "a"
        assert result_a["x"] == "hello"

        result_b = json.loads(await captured_coroutines[1](y=99))
        assert result_b["tool"] == "b"
        assert result_b["y"] == 99
