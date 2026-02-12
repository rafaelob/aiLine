"""Tests for shared.container -- DI container build."""

from __future__ import annotations

from ailine_runtime.shared.config import Settings
from ailine_runtime.shared.container import Container


class TestContainer:
    def test_build_returns_container(self):
        settings = Settings()
        container = Container.build(settings)
        assert isinstance(container, Container)
        assert container.settings is settings

    def test_event_bus_is_inmemory(self):
        from ailine_runtime.adapters.events.inmemory_bus import InMemoryEventBus

        # Force the default localhost Redis URL so _build_event_bus treats it
        # as "not configured" and returns InMemoryEventBus. In Docker,
        # AILINE_REDIS_URL points at the real Redis service.
        settings = Settings(redis={"url": "redis://localhost:6379/0"})
        container = Container.build(settings)
        assert isinstance(container.event_bus, InMemoryEventBus)

    def test_container_is_frozen(self):
        settings = Settings()
        container = Container.build(settings)
        import pytest

        with pytest.raises(AttributeError):
            container.settings = settings  # type: ignore[misc]

    def test_llm_defaults_to_fake_when_no_key(self):
        """ADR-051: Without API keys, container provides FakeChatLLM (not None)."""
        from unittest.mock import patch

        from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM

        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(
                anthropic_api_key="",
                openai_api_key="",
                google_api_key="",
                openrouter_api_key="",
            )
            container = Container.build(settings)
            assert isinstance(container.llm, FakeChatLLM)
            assert container.embeddings is None
            assert container.vectorstore is None
