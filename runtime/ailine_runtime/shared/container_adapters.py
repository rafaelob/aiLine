"""Adapter factory functions for the DI container.

Builds concrete adapter instances from Settings. Each function handles
graceful degradation: missing API keys or optional dependencies fall
back to fake/in-memory implementations (ADR-051).

Split from container.py for single-responsibility (container_core has
the Container dataclass; this module has adapter resolution logic).
"""

from __future__ import annotations

import logging
from typing import Any

from ..domain.ports.embeddings import Embeddings
from ..domain.ports.events import EventBus
from ..domain.ports.llm import ChatLLM
from ..domain.ports.media import (
    STT,
    TTS,
    ImageDescriber,
    OCRProcessor,
    SignRecognition,
)
from ..domain.ports.vectorstore import VectorStore
from .config import Settings

_log = logging.getLogger("ailine.container")


def build_vectorstore(settings: Settings, cleanup: list[Any]) -> VectorStore | None:
    """Build vector store adapter based on provider setting.

    Returns None when the required database URL is not configured (e.g. SQLite dev).
    When a SQLAlchemy engine is created, its reference is appended to the
    ``cleanup`` list so the Container can dispose it on shutdown.
    """
    provider = settings.vectorstore.provider
    if provider == "pgvector":
        db_url = settings.db.url
        # pgvector requires a PostgreSQL URL
        if not db_url or "sqlite" in db_url:
            return None
        try:
            from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

            from ..adapters.vectorstores.pgvector_store import PgVectorStore

            engine = create_async_engine(
                db_url,
                pool_size=settings.db.pool_size,
                max_overflow=settings.db.max_overflow,
                echo=settings.db.echo,
            )
            # Track engine for graceful shutdown and pool monitoring
            cleanup.append(engine)

            # Auto-instrument SQLAlchemy with OpenTelemetry if enabled
            from .tracing import instrument_sqlalchemy

            instrument_sqlalchemy(engine.sync_engine)

            _log.info(
                "container.engine_created pool_size=%d max_overflow=%d pool_class=%s",
                settings.db.pool_size,
                settings.db.max_overflow,
                type(engine.pool).__name__,
            )
            session_factory = async_sessionmaker(engine, expire_on_commit=False)
            return PgVectorStore(
                session_factory=session_factory,
                dimensions=settings.embedding.dimensions,
            )
        except ImportError:
            return None
    return None


def build_event_bus(settings: Settings) -> EventBus:
    """Build event bus: in-memory for dev, Redis for prod.

    Uses AILINE_EVENT_BUS_PROVIDER setting (redis|inmemory) when set,
    otherwise falls back to detecting a non-empty redis URL.
    """
    import os

    explicit_provider = os.getenv("AILINE_EVENT_BUS_PROVIDER", "").lower()
    redis_url = settings.redis.url

    use_redis = explicit_provider == "redis" or (explicit_provider == "" and bool(redis_url))

    if use_redis and redis_url:
        try:
            from ..adapters.events.redis_bus import RedisEventBus

            return RedisEventBus(redis_url=redis_url)
        except ImportError:
            _log.warning("container.redis_import_failed: falling back to InMemoryEventBus")

    from ..adapters.events.inmemory_bus import InMemoryEventBus

    return InMemoryEventBus()


def build_llm(settings: Settings) -> ChatLLM:
    """Build LLM adapter based on provider setting."""
    provider = settings.llm.provider
    api_key = settings.llm.api_key or resolve_api_key(settings, provider)
    model = settings.llm.model

    # ADR-051: Fall back to FakeLLM when no API key is configured
    if not api_key and provider != "fake":
        from ..adapters.llm.fake_llm import FakeChatLLM

        return FakeChatLLM(model=model)

    if provider == "anthropic":
        from ..adapters.llm.anthropic_llm import AnthropicChatLLM

        return AnthropicChatLLM(model=model, api_key=api_key)
    if provider == "openai" or provider == "openrouter":
        from ..adapters.llm.openai_llm import OpenAIChatLLM

        return OpenAIChatLLM(model=model, api_key=api_key, provider=provider)
    if provider == "gemini":
        from ..adapters.llm.gemini_llm import GeminiChatLLM

        return GeminiChatLLM(model=model, api_key=api_key)
    # Fallback to FakeLLM for testing / no-key scenarios
    from ..adapters.llm.fake_llm import FakeChatLLM

    return FakeChatLLM(model=model)


def build_embeddings(settings: Settings) -> Embeddings | None:
    """Build embeddings adapter based on provider setting."""
    provider = settings.embedding.provider
    api_key = settings.embedding.api_key or resolve_api_key(settings, provider)

    if not api_key:
        # No API key -- return None (embeddings unavailable until configured)
        return None

    if provider == "gemini":
        from ..adapters.embeddings.gemini_embeddings import GeminiEmbeddings

        return GeminiEmbeddings(
            model=settings.embedding.model,
            api_key=api_key,
            dimensions=settings.embedding.dimensions,
        )
    if provider == "openai":
        from ..adapters.embeddings.openai_embeddings import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=settings.embedding.model,
            api_key=api_key,
            dimensions=settings.embedding.dimensions,
        )
    return None


def build_media(
    settings: Settings,
) -> tuple[STT, TTS, ImageDescriber, OCRProcessor]:
    """Build media adapters (STT, TTS, ImageDescriber, OCR).

    Falls back to fake implementations when no API keys are configured
    or when the optional dependencies are not installed (ADR-051).
    """
    from ..adapters.media.fake_image_describer import FakeImageDescriber
    from ..adapters.media.fake_stt import FakeSTT
    from ..adapters.media.fake_tts import FakeTTS
    from ..adapters.media.ocr_processor import OCRProcessor as OCRProcessorAdapter

    # STT: prefer OpenAI cloud when key available, else Whisper local, else fake
    stt: STT
    openai_key = settings.openai_api_key
    if openai_key:
        try:
            from ..adapters.media.openai_stt import OpenAISTT

            stt = OpenAISTT(api_key=openai_key)
        except ImportError:
            stt = FakeSTT()
    else:
        try:
            from ..adapters.media.whisper_stt import WhisperSTT

            stt = WhisperSTT()
        except ImportError:
            stt = FakeSTT()

    # TTS: prefer ElevenLabs when key available, else fake
    tts: TTS
    elevenlabs_key = getattr(settings, "elevenlabs_api_key", "")
    if elevenlabs_key:
        from ..adapters.media.elevenlabs_tts import ElevenLabsTTS

        tts = ElevenLabsTTS(api_key=elevenlabs_key)
    else:
        tts = FakeTTS()

    # Image describer: fake for now (real impl needs vision LLM, Sprint 9)
    image_describer: ImageDescriber = FakeImageDescriber()

    # OCR: always available (graceful degradation via lazy imports)
    ocr: OCRProcessor = OCRProcessorAdapter()

    return stt, tts, image_describer, ocr


def build_sign_recognition(settings: Settings) -> SignRecognition:
    """Build sign recognition adapter.

    Uses FakeSignRecognition by default (ADR-026, ADR-051).
    When a model file is configured, attempts to load MediaPipeSignRecognition;
    falls back to fake on import failure (optional dependency).
    """
    model_path = getattr(settings, "sign_model_path", "")
    if model_path:
        try:
            from ..adapters.media.sign_recognition import MediaPipeSignRecognition

            return MediaPipeSignRecognition(model_path=model_path)
        except ImportError:
            _log.warning("container.sign_recognition_import_failed: falling back to FakeSignRecognition")

    from ..adapters.media.fake_sign_recognition import FakeSignRecognition

    return FakeSignRecognition()


def resolve_api_key(settings: Settings, provider: str) -> str:
    """Resolve API key from top-level settings based on provider."""
    mapping = {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "gemini": settings.google_api_key,
        "openrouter": settings.openrouter_api_key,
    }
    return mapping.get(provider, "")
