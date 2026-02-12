"""Fake tool dispatcher for testing executor tool calls.

Records all tool invocations and returns configurable responses.
Useful for verifying that the executor calls tools correctly
without hitting real implementations (ADR-051).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    """Record of a single tool invocation."""

    tool_name: str
    args: dict[str, Any]


class FakeToolDispatcher:
    """Records tool calls and returns configurable responses.

    Usage::

        dispatcher = FakeToolDispatcher(
            responses={
                "rag_search": {"chunks": [], "note": "fake"},
                "save_plan": {"plan_id": "test-123", "stored_at": "/tmp"},
            }
        )

        result = await dispatcher.dispatch("rag_search", {"query": "fractions"})
        assert dispatcher.calls[0].tool_name == "rag_search"

    If no response mapping exists for a tool, returns a default
    ``{"status": "ok", "tool_name": <name>}`` response.
    """

    def __init__(
        self,
        *,
        responses: dict[str, Any] | None = None,
    ) -> None:
        self._responses = responses or {}
        self.calls: list[ToolCall] = []

    async def dispatch(self, tool_name: str, args: dict[str, Any]) -> Any:
        """Dispatch a tool call, recording it and returning a configured response."""
        self.calls.append(ToolCall(tool_name=tool_name, args=args))
        if tool_name in self._responses:
            return self._responses[tool_name]
        return {"status": "ok", "tool_name": tool_name}

    def reset(self) -> None:
        """Clear recorded calls."""
        self.calls.clear()

    @property
    def call_count(self) -> int:
        return len(self.calls)

    def calls_for(self, tool_name: str) -> list[ToolCall]:
        """Return all recorded calls for a specific tool."""
        return [c for c in self.calls if c.tool_name == tool_name]
