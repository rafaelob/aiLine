"""SSE (Server-Sent Events) helpers for streaming pipeline progress."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any


def format_sse_event(event_type: str, data: dict[str, Any]) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def heartbeat_generator(interval: float = 15.0) -> AsyncIterator[str]:
    """Generate periodic heartbeat events to keep connection alive."""
    import asyncio

    while True:
        await asyncio.sleep(interval)
        yield format_sse_event("heartbeat", {"status": "alive"})
