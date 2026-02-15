"""Tests for ToolDef -> Pydantic AI tool bridge conversion."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from ailine_agents.agents._tool_bridge import register_tool, register_tools
from ailine_agents.deps import AgentDeps

# -- Test args models -------------------------------------------------------


class SimpleArgs(BaseModel):
    query: str = Field(..., description="Search query")
    k: int = Field(5, description="Number of results")


class ArgsWithTeacherId(BaseModel):
    query: str = Field(..., description="Search query")
    teacher_id: str | None = Field(None, description="Teacher scope")


# -- Fake ToolDef (mirrors runtime ToolDef without importing it) ------------


class _FakeToolDef:
    """Minimal stand-in for runtime ToolDef (dataclass)."""

    def __init__(self, name: str, description: str, args_model: type[BaseModel], handler: Any) -> None:
        self.name = name
        self.description = description
        self.args_model = args_model
        self.handler = handler


class TestRegisterTool:
    """register_tool() converts a ToolDef and adds it to a Pydantic AI agent."""

    def test_tool_registered_on_agent(self) -> None:
        agent: Agent[AgentDeps, str] = Agent(
            "test",
            output_type=str,
            deps_type=AgentDeps,
        )
        handler = AsyncMock(return_value={"chunks": []})
        tool_def = _FakeToolDef("my_tool", "My test tool", SimpleArgs, handler)

        initial_tool_count = len(agent._function_toolset.tools)
        register_tool(agent, tool_def)
        assert len(agent._function_toolset.tools) == initial_tool_count + 1
        assert "my_tool" in agent._function_toolset.tools

    def test_tool_metadata_set(self) -> None:
        agent: Agent[AgentDeps, str] = Agent(
            "test",
            output_type=str,
            deps_type=AgentDeps,
        )
        handler = AsyncMock(return_value={})
        tool_def = _FakeToolDef("search_tool", "Busca materiais", SimpleArgs, handler)

        register_tool(agent, tool_def)
        tool = agent._function_toolset.tools["search_tool"]
        assert tool.name == "search_tool"


class TestRegisterTools:
    """register_tools() registers multiple ToolDefs with optional filtering."""

    def _make_tools(self) -> list[_FakeToolDef]:
        return [
            _FakeToolDef("tool_a", "Tool A", SimpleArgs, AsyncMock(return_value={})),
            _FakeToolDef("tool_b", "Tool B", SimpleArgs, AsyncMock(return_value={})),
            _FakeToolDef("tool_c", "Tool C", ArgsWithTeacherId, AsyncMock(return_value={})),
        ]

    def test_register_all(self) -> None:
        agent: Agent[AgentDeps, str] = Agent("test", output_type=str, deps_type=AgentDeps)
        tools = self._make_tools()

        register_tools(agent, tools)
        assert "tool_a" in agent._function_toolset.tools
        assert "tool_b" in agent._function_toolset.tools
        assert "tool_c" in agent._function_toolset.tools

    def test_register_filtered(self) -> None:
        agent: Agent[AgentDeps, str] = Agent("test", output_type=str, deps_type=AgentDeps)
        tools = self._make_tools()

        register_tools(agent, tools, allowed_names=["tool_a", "tool_c"])
        assert "tool_a" in agent._function_toolset.tools
        assert "tool_b" not in agent._function_toolset.tools
        assert "tool_c" in agent._function_toolset.tools

    def test_register_empty_allowed_names(self) -> None:
        agent: Agent[AgentDeps, str] = Agent("test", output_type=str, deps_type=AgentDeps)
        tools = self._make_tools()

        register_tools(agent, tools, allowed_names=[])
        assert len(agent._function_toolset.tools) == 0

    def test_register_none_allowed_names_registers_all(self) -> None:
        agent: Agent[AgentDeps, str] = Agent("test", output_type=str, deps_type=AgentDeps)
        tools = self._make_tools()

        register_tools(agent, tools, allowed_names=None)
        assert len(agent._function_toolset.tools) == 3
