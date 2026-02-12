"""Tests for adapters.events.inmemory_bus -- in-process async event bus."""

from __future__ import annotations

import pytest

from ailine_runtime.adapters.events.inmemory_bus import InMemoryEventBus
from ailine_runtime.domain.ports.events import EventBus


class TestInMemoryEventBus:
    def test_conforms_to_protocol(self):
        bus = InMemoryEventBus()
        assert isinstance(bus, EventBus)

    @pytest.mark.asyncio
    async def test_publish_delivers_to_subscriber(self):
        bus = InMemoryEventBus()
        received: list[dict] = []

        async def handler(data: dict) -> None:
            received.append(data)

        bus.subscribe("test.event", handler)
        await bus.publish("test.event", {"key": "value"})

        assert len(received) == 1
        assert received[0] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self):
        bus = InMemoryEventBus()
        # Should not raise
        await bus.publish("nobody.listening", {"data": 1})

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self):
        bus = InMemoryEventBus()
        calls: list[str] = []

        async def handler_a(data: dict) -> None:
            calls.append("a")

        async def handler_b(data: dict) -> None:
            calls.append("b")

        bus.subscribe("multi", handler_a)
        bus.subscribe("multi", handler_b)
        await bus.publish("multi", {})

        assert calls == ["a", "b"]

    @pytest.mark.asyncio
    async def test_handler_error_does_not_propagate(self):
        bus = InMemoryEventBus()
        calls: list[str] = []

        async def bad_handler(data: dict) -> None:
            raise RuntimeError("boom")

        async def good_handler(data: dict) -> None:
            calls.append("ok")

        bus.subscribe("err", bad_handler)
        bus.subscribe("err", good_handler)
        await bus.publish("err", {})

        # The good handler should still have been called
        assert calls == ["ok"]

    @pytest.mark.asyncio
    async def test_different_event_types_isolated(self):
        bus = InMemoryEventBus()
        received_a: list[dict] = []
        received_b: list[dict] = []

        async def handler_a(data: dict) -> None:
            received_a.append(data)

        async def handler_b(data: dict) -> None:
            received_b.append(data)

        bus.subscribe("type_a", handler_a)
        bus.subscribe("type_b", handler_b)

        await bus.publish("type_a", {"src": "a"})
        await bus.publish("type_b", {"src": "b"})

        assert len(received_a) == 1
        assert received_a[0]["src"] == "a"
        assert len(received_b) == 1
        assert received_b[0]["src"] == "b"
