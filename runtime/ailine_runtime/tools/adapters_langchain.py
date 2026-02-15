from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import StructuredTool

from .registry import ToolDef


def to_langchain_tools(registry: list[ToolDef]) -> list[StructuredTool]:
    """Converte ToolDef → LangChain StructuredTool (compatível com DeepAgents)."""
    tools: list[StructuredTool] = []

    for t in registry:

        async def _run(_t: ToolDef = t, **kwargs: Any) -> str:
            parsed = _t.args_model(**kwargs)
            result = await _t.handler(parsed)
            return json.dumps(result, ensure_ascii=False)

        tools.append(
            StructuredTool.from_function(
                name=t.name,
                description=t.description,
                args_schema=t.args_model,
                coroutine=_run,
            )
        )

    return tools
