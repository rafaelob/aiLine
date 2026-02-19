"""Port: event bus for publish/subscribe."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EventBus(Protocol):
    """Protocol for event publishing/subscribing."""

    async def publish(self, event_type: str, data: dict[str, Any]) -> None: ...

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None: ...

    async def ping(self) -> bool:
        """Health check: return True if the bus is reachable."""
        ...
