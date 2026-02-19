from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from ...shared.observability import get_logger

_log = get_logger("ailine.events.inmemory")


class InMemoryEventBus:
    """In-process async event bus for development."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[dict[str, Any]], Awaitable[None]]]] = (
            defaultdict(list)
        )

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        for handler in self._handlers.get(event_type, []):
            try:
                await handler(data)
            except Exception:
                _log.exception("event_handler_failed", event_type=event_type)

    def subscribe(
        self, event_type: str, handler: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        self._handlers[event_type].append(handler)

    async def ping(self) -> bool:
        """In-memory bus is always reachable."""
        return True
