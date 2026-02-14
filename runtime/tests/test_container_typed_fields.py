"""Tests for FINDING-01: Container fields typed to port Protocols."""

from __future__ import annotations

from unittest.mock import patch

from ailine_runtime.domain.ports.events import EventBus
from ailine_runtime.domain.ports.llm import ChatLLM
from ailine_runtime.shared.config import (
    DatabaseConfig,
    EmbeddingConfig,
    LLMConfig,
    Settings,
)
from ailine_runtime.shared.container import Container


class TestContainerTypedFields:
    def test_llm_field_conforms_to_chatllm_protocol(self):
        settings = Settings(llm=LLMConfig(provider="fake", api_key=""))
        container = Container.build(settings)
        assert isinstance(container.llm, ChatLLM)

    def test_event_bus_field_conforms_to_eventbus_protocol(self):
        settings = Settings()
        container = Container.build(settings)
        assert isinstance(container.event_bus, EventBus)

    def test_embeddings_none_when_no_key(self):
        settings = Settings(embedding=EmbeddingConfig(provider="gemini", api_key=""))
        container = Container.build(settings)
        assert container.embeddings is None

    def test_vectorstore_none_with_sqlite(self):
        """Vectorstore returns None when the DB URL is SQLite (not PostgreSQL)."""
        settings = Settings(db=DatabaseConfig(url="sqlite+aiosqlite:///./dev.db"))
        container = Container.build(settings)
        assert container.vectorstore is None

    def test_container_build_all_fields_populated(self):
        with patch.dict("os.environ", {}, clear=False):
            settings = Settings()
            container = Container.build(settings)
            # Core fields
            assert container.settings is settings
            assert container.llm is not None
            assert container.event_bus is not None
            # Media fields
            assert container.stt is not None
            assert container.tts is not None
            assert container.image_describer is not None
            assert container.ocr is not None
            assert container.sign_recognition is not None
