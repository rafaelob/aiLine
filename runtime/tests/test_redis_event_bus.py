"""Tests for FINDING-11: RedisEventBus and event bus selection in container."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ailine_runtime.adapters.events.inmemory_bus import InMemoryEventBus
from ailine_runtime.shared.config import Settings
from ailine_runtime.shared.container_adapters import build_event_bus as _build_event_bus


class TestRedisEventBus:
    def test_conforms_to_protocol(self):
        """RedisEventBus satisfies the EventBus protocol (structural)."""
        mock_redis_mod = MagicMock()
        mock_redis_class = MagicMock()
        mock_redis_mod.Redis = mock_redis_class
        mock_redis_mod.asyncio.Redis = mock_redis_class

        with patch.dict(sys.modules, {"redis": mock_redis_mod, "redis.asyncio": mock_redis_mod}):
            from ailine_runtime.adapters.events.redis_bus import RedisEventBus

            bus = RedisEventBus(redis_url="redis://localhost:6379/0")
            assert hasattr(bus, "publish")
            assert hasattr(bus, "subscribe")

    @pytest.mark.asyncio
    async def test_publish_calls_local_handlers(self):
        """Local handlers receive events even with Redis backing."""
        mock_redis_mod = MagicMock()
        mock_redis_instance = AsyncMock()
        mock_redis_mod.Redis.from_url.return_value = mock_redis_instance

        with patch.dict(sys.modules, {"redis": mock_redis_mod, "redis.asyncio": mock_redis_mod}):
            from ailine_runtime.adapters.events.redis_bus import RedisEventBus

            bus = RedisEventBus(redis_url="redis://localhost:6379/0")

            received: list[dict] = []

            async def handler(data: dict) -> None:
                received.append(data)

            bus.subscribe("test.event", handler)
            await bus.publish("test.event", {"key": "value"})

            assert len(received) == 1
            assert received[0] == {"key": "value"}
            # Redis publish was also called
            mock_redis_instance.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self):
        """Publishing to an event with no subscribers should not raise."""
        mock_redis_mod = MagicMock()
        mock_redis_instance = AsyncMock()
        mock_redis_mod.Redis.from_url.return_value = mock_redis_instance

        with patch.dict(sys.modules, {"redis": mock_redis_mod, "redis.asyncio": mock_redis_mod}):
            from ailine_runtime.adapters.events.redis_bus import RedisEventBus

            bus = RedisEventBus(redis_url="redis://localhost:6379/0")
            await bus.publish("nobody.listening", {"data": 1})

    @pytest.mark.asyncio
    async def test_handler_error_does_not_propagate(self):
        """If a handler raises, other handlers still run."""
        mock_redis_mod = MagicMock()
        mock_redis_instance = AsyncMock()
        mock_redis_mod.Redis.from_url.return_value = mock_redis_instance

        with patch.dict(sys.modules, {"redis": mock_redis_mod, "redis.asyncio": mock_redis_mod}):
            from ailine_runtime.adapters.events.redis_bus import RedisEventBus

            bus = RedisEventBus(redis_url="redis://localhost:6379/0")
            calls: list[str] = []

            async def bad_handler(data: dict) -> None:
                raise RuntimeError("boom")

            async def good_handler(data: dict) -> None:
                calls.append("ok")

            bus.subscribe("err", bad_handler)
            bus.subscribe("err", good_handler)
            await bus.publish("err", {})

            assert calls == ["ok"]


class TestEventBusSelection:
    def test_empty_redis_url_uses_inmemory(self):
        """An empty redis URL means 'not configured' -> InMemoryEventBus."""
        settings = Settings(redis={"url": ""})
        bus = _build_event_bus(settings)
        assert isinstance(bus, InMemoryEventBus)

    def test_custom_redis_url_attempts_redis_bus(self):
        """A non-default Redis URL triggers RedisEventBus creation."""
        mock_redis_mod = MagicMock()
        mock_redis_instance = AsyncMock()
        mock_redis_mod.Redis.from_url.return_value = mock_redis_instance

        settings = Settings(redis={"url": "redis://prod-redis:6379/1"})

        with patch.dict(sys.modules, {"redis": mock_redis_mod, "redis.asyncio": mock_redis_mod}):
            bus = _build_event_bus(settings)
            assert type(bus).__name__ == "RedisEventBus"

    def test_redis_import_error_falls_back_to_inmemory(self):
        """If redis package is not installed, fall back to InMemoryEventBus."""
        settings = Settings(redis={"url": "redis://prod-redis:6379/1"})

        # Block the redis_bus module import
        redis_bus_key = "ailine_runtime.adapters.events.redis_bus"
        saved = sys.modules.get(redis_bus_key)
        try:
            sys.modules[redis_bus_key] = None  # type: ignore[assignment]
            bus = _build_event_bus(settings)
            assert isinstance(bus, InMemoryEventBus)
        finally:
            if saved is not None:
                sys.modules[redis_bus_key] = saved
            else:
                sys.modules.pop(redis_bus_key, None)
