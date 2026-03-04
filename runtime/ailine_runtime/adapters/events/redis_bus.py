"""Redis PubSub-based event bus for production use.

Implements the EventBus protocol using redis-py async PubSub.
Falls back to InMemoryEventBus when redis is unavailable (ADR-054).
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from ...shared.observability import get_logger

_log = get_logger("ailine.events.redis")


class RedisEventBus:
    """EventBus implementation backed by Redis PubSub."""

    def __init__(self, *, redis_url: str = "redis://localhost:6379/0") -> None:
        from redis.asyncio import Redis

        self._redis: Redis = Redis.from_url(redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        self._handlers: dict[str, list[Callable[[dict[str, Any]], Awaitable[None]]]] = (
            defaultdict(list)
        )
        self._listener_task: asyncio.Task[None] | None = None

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        payload = json.dumps(
            {"event_type": event_type, "data": data}, ensure_ascii=False
        )
        await self._redis.publish(event_type, payload)

        # Also dispatch to local in-process handlers (same-node subscribers)
        for handler in self._handlers.get(event_type, []):
            try:
                await handler(data)
            except Exception:
                _log.exception("event_handler_failed", event_type=event_type)

    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        self._handlers[event_type].append(handler)
        await self._pubsub.subscribe(event_type)
        if self._listener_task is None or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        """Background listener that dispatches PubSub messages to handlers."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    payload = json.loads(message["data"])
                    event_type = payload.get("event_type", "")
                    data = payload.get("data", {})
                    for handler in self._handlers.get(event_type, []):
                        try:
                            await handler(data)
                        except Exception:
                            _log.exception("event_handler_failed", event_type=event_type)
                except (json.JSONDecodeError, KeyError):
                    _log.warning("invalid_pubsub_message", data=message.get("data"))
        except asyncio.CancelledError:
            return
        except Exception:
            _log.exception("pubsub_listener_crashed")

    async def ping(self) -> bool:
        """Check Redis connectivity."""
        try:
            return bool(await self._redis.ping())
        except Exception:
            return False

    async def get_redis_client(self) -> Any | None:
        """Return the underlying Redis client for direct access (jti blacklist, etc.)."""
        return self._redis

    async def close(self) -> None:
        """Gracefully shut down the Redis connection."""
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
        await self._pubsub.aclose()
        await self._redis.aclose()
