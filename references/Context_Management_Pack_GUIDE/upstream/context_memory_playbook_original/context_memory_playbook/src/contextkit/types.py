from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


Message = dict  # {"role": "system|developer|user|assistant|tool", "content": "..."}


@dataclass
class ToolCall:
    """A tool call request."""
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    server_id: Optional[str] = None  # for MCP tools
    call_id: Optional[str] = None


@dataclass
class ToolResult:
    """A tool result (raw payload can be large; avoid keeping it inline)."""
    name: str
    content: Any
    server_id: Optional[str] = None
    call_id: Optional[str] = None
    is_error: bool = False


@dataclass
class Turn:
    """A conversation turn (unit of trimming/compaction).

    A turn is treated as an atomic bundle to prevent breaking dependencies:
      user msg -> tool calls/results -> assistant msg
    """
    user: Message
    assistant: Optional[Message] = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)

    def to_messages(self) -> list[Message]:
        msgs: list[Message] = [self.user]
        for r in self.tool_results:
            msgs.append({"role": "tool", "content": str(r.content), "name": r.name})
        if self.assistant:
            msgs.append(self.assistant)
        return msgs
