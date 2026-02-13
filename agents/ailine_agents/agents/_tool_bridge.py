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
import typing
from typing import Any, Union, get_args, get_origin

from pydantic_ai import Agent, RunContext

from ..deps import AgentDeps

# OTEL tracing -- optional; no-op when runtime tracing is unavailable
try:
    from ailine_runtime.shared.tracing import trace_tool_call as _trace_tool_call
except ImportError:
    _trace_tool_call = None

# Pydantic JSON Schema type -> Python annotation mapping (fallback)
_TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _resolve_annotation(field_info: Any, prop: dict[str, Any]) -> Any:
    """Resolve the best Python annotation for a tool parameter.

    Prefers the Pydantic field annotation (preserves enums, Optional,
    nested models, constrained types). Falls back to JSON schema type
    mapping only when the annotation is unavailable.
    """
    ann = getattr(field_info, "annotation", None)
    if ann is not None and ann is not Any:
        # Unwrap Optional[X] to X for the signature (Pydantic AI handles
        # optionality via defaults, not via Union[X, None] in annotations)
        origin = get_origin(ann)
        if origin is Union:
            args = [a for a in get_args(ann) if a is not type(None)]
            if len(args) == 1:
                return args[0]
        return ann
    return _TYPE_MAP.get(prop.get("type", "string"), Any)


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
        # Skip teacher_id — auto-injected from deps (only when optional)
        if field_name == "teacher_id" and not getattr(field_info, "is_required", lambda: True)():
            continue

        prop = properties.get(field_name, {})
        annotation = _resolve_annotation(field_info, prop)

        # Use Pydantic field metadata for default handling
        is_required = getattr(field_info, "is_required", None)
        if callable(is_required) and is_required():
            default = inspect.Parameter.empty
        elif field_info.default is not None:
            default = field_info.default
        elif getattr(field_info, "default_factory", None) is not None:
            default = None  # factory will fill at model init
        else:
            default = None

        params.append(
            inspect.Parameter(
                field_name,
                inspect.Parameter.KEYWORD_ONLY,
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

        if _trace_tool_call is not None:
            import time as _time

            with _trace_tool_call(tool_name=tool_def.name) as span_data:
                _t0 = _time.monotonic()
                result = await tool_def.handler(parsed_args)
                span_data["latency_ms"] = (_time.monotonic() - _t0) * 1000
                return result
        return await tool_def.handler(parsed_args)

    _tool_fn.__signature__ = sig  # type: ignore[attr-defined]
    _tool_fn.__annotations__ = annotations
    _tool_fn.__name__ = tool_def.name
    _tool_fn.__doc__ = tool_def.description
    _tool_fn.__qualname__ = f"_tool_bridge.{tool_def.name}"
    # Pydantic AI uses __module__ for get_type_hints globalns lookup
    _tool_fn.__module__ = __name__

    # Fail-fast: verify patched signature is readable by inspection APIs.
    # Catches breakage early if Pydantic AI changes its introspection logic.
    try:
        inspect.signature(_tool_fn)
        typing.get_type_hints(_tool_fn, include_extras=True)
    except Exception as exc:
        raise RuntimeError(
            f"Tool bridge self-check failed for '{tool_def.name}': {exc}. "
            f"Pydantic AI inspection may have changed."
        ) from exc

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
