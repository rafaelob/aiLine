"""Tests for tools/adapters_langchain.py.

Uses attribute-level patching to avoid module caching issues in full suite runs.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from ailine_runtime.tools.registry import ToolDef


class MockArgs(BaseModel):
    query: str = Field(..., description="Test query")


async def mock_handler(args: MockArgs) -> dict:
    return {"result": args.query}


@pytest.fixture
def sample_registry():
    return [
        ToolDef(
            name="test_tool",
            description="A test tool",
            args_model=MockArgs,
            handler=mock_handler,
        )
    ]


class TestLangChainAdapters:
    def test_to_langchain_tools(self, sample_registry):
        """Test converting ToolDef to LangChain StructuredTools.

        Uses attribute-level patching since langchain_core is already loaded
        by langgraph; importlib.reload would break the existing module state.
        """
        import ailine_runtime.tools.adapters_langchain as lc_mod

        mock_structured_tool = MagicMock()

        with patch.object(lc_mod, "StructuredTool", mock_structured_tool):
            tools = lc_mod.to_langchain_tools(sample_registry)
            assert len(tools) == 1
            mock_structured_tool.from_function.assert_called_once()
            call_kwargs = mock_structured_tool.from_function.call_args
            assert call_kwargs.kwargs["name"] == "test_tool"
