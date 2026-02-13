"""Bridge: ToolDef (runtime registry) -> Pydantic AI agent tools.

Converts existing ToolDef handler functions into Pydantic AI tool functions
that receive RunContext[AgentDeps]. Automatically injects teacher_id from
deps for tenant-scoped execution.

Builds proper function signatures and annotations so Pydantic AI can
auto-generate correct JSON schemas for LLM tool calling.
"""

# NOTE: Do NOT use `from __future__ import annotations` here.
# Pydantic AI uses get_type_hints() which needs real type objects
# in __annotations__, not stringified forward references.

import inspect
from typing import Any

from pydantic_ai import Agent, RunContext

from ..deps import AgentDeps

# Pydantic JSON Schema type -> Python annotation mapping
_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _build_typed_wrapper(tool_def: Any) -> Any:
    """Build a wrapper function with proper typed signature from ToolDef.args_model.

    Pydantic AI introspects function annotations for tool parameter discovery.
    A ``**kwargs`` signature loses all type info. This function dynamically
    creates parameters and annotations from the Pydantic model fields so the
    LLM receives correct JSON schemas.
    """
    schema = tool_def.args_model.model_json_schema()
    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))
    model_fields = tool_def.args_model.model_fields

    # Build inspect.Parameter list and annotations dict
    params: list[inspect.Parameter] = [
        inspect.Parameter(
            "ctx",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=RunContext[AgentDeps],
        ),
    ]
    annotations: dict[str, Any] = {"ctx": RunContext[AgentDeps], "return": Any}

    for field_name, field_info in model_fields.items():
        # Skip teacher_id — auto-injected from deps
        if field_name == "teacher_id":
            continue

        prop = properties.get(field_name, {})
        annotation = _TYPE_MAP.get(prop.get("type", "string"), Any)

        # Use field default if available, otherwise EMPTY for required
        if field_name in required_fields:
            default = inspect.Parameter.empty
        elif field_info.default is not None:
            default = field_info.default
        else:
            default = None

        params.append(
            inspect.Parameter(
                field_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=annotation,
            )
        )
        annotations[field_name] = annotation

    sig = inspect.Signature(params)

    async def _tool_fn(ctx: RunContext[AgentDeps], **kwargs: Any) -> Any:
        # Auto-inject teacher_id if the tool's args model declares it
        args_fields = tool_def.args_model.model_fields
        if "teacher_id" in args_fields and "teacher_id" not in kwargs:
            kwargs["teacher_id"] = ctx.deps.teacher_id

        parsed_args = tool_def.args_model(**kwargs)
        return await tool_def.handler(parsed_args)

    _tool_fn.__signature__ = sig  # type: ignore[attr-defined]
    _tool_fn.__annotations__ = annotations
    _tool_fn.__name__ = tool_def.name
    _tool_fn.__doc__ = tool_def.description
    _tool_fn.__qualname__ = f"_tool_bridge.{tool_def.name}"
    # Pydantic AI uses __module__ for get_type_hints globalns lookup
    _tool_fn.__module__ = __name__

    return _tool_fn


def register_tool(agent: Agent[AgentDeps, Any], tool_def: Any) -> None:
    """Register a single ToolDef as a Pydantic AI tool on the agent."""
    wrapper = _build_typed_wrapper(tool_def)
    agent.tool(wrapper)


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
