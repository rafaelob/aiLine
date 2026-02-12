"""Bridge: ToolDef (runtime registry) -> Pydantic AI agent tools.

Converts existing ToolDef handler functions into Pydantic AI tool functions
that receive RunContext[AgentDeps]. Automatically injects teacher_id from
deps for tenant-scoped execution.
"""

from __future__ import annotations

from typing import Any

from pydantic_ai import Agent, RunContext

from ..deps import AgentDeps


def register_tool(agent: Agent[AgentDeps, Any], tool_def: Any) -> None:
    """Register a single ToolDef as a Pydantic AI tool on the agent.

    The bridge:
    1. Creates a wrapper with correct signature
    2. Injects teacher_id from RunContext deps into tool args
    3. Calls the original async handler
    """

    async def _tool_fn(ctx: RunContext[AgentDeps], **kwargs: Any) -> Any:
        # Auto-inject teacher_id if the tool's args model declares it
        args_fields = tool_def.args_model.model_fields
        if "teacher_id" in args_fields and "teacher_id" not in kwargs:
            kwargs["teacher_id"] = ctx.deps.teacher_id

        parsed_args = tool_def.args_model(**kwargs)
        return await tool_def.handler(parsed_args)

    # Build a JSON schema from the args model for the tool parameters
    schema = tool_def.args_model.model_json_schema()
    properties = schema.get("properties", {})
    schema.get("required", [])

    # Build parameter descriptions for the tool
    param_descriptions = []
    for name, prop in properties.items():
        desc = prop.get("description", "")
        if desc:
            param_descriptions.append(f"  - {name}: {desc}")

    full_description = tool_def.description
    if param_descriptions:
        full_description += "\n\nParameters:\n" + "\n".join(param_descriptions)

    # Set function metadata for Pydantic AI tool discovery
    _tool_fn.__name__ = tool_def.name
    _tool_fn.__doc__ = full_description
    _tool_fn.__qualname__ = f"_tool_bridge.{tool_def.name}"

    agent.tool(_tool_fn)


def register_tools(
    agent: Agent[AgentDeps, Any],
    tool_defs: list[Any],
    *,
    allowed_names: list[str] | None = None,
) -> None:
    """Register multiple ToolDefs on an agent, optionally filtering by name."""
    for td in tool_defs:
        if allowed_names is None or td.name in allowed_names:
            register_tool(agent, td)
