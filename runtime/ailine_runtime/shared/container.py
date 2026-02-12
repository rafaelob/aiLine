from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..domain.ports.embeddings import Embeddings
from ..domain.ports.events import EventBus
from ..domain.ports.llm import ChatLLM
from ..domain.ports.media import STT, TTS, ImageDescriber, SignRecognition
from ..domain.ports.vectorstore import VectorStore
from .config import Settings


@dataclass(frozen=True)
class Container:
    """Lightweight DI container. Built once at startup, immutable during requests."""

    settings: Settings

    # Resolved port implementations (populated by build())
    llm: ChatLLM | None = None
    embeddings: Embeddings | None = None
    vectorstore: VectorStore | None = None
    event_bus: EventBus | None = None

    # Media adapters (STT, TTS, image description, OCR, sign recognition)
    stt: STT | None = None
    tts: TTS | None = None
    image_describer: ImageDescriber | None = None
    ocr: Any = None  # OCRProcessor does not implement a port protocol yet
    sign_recognition: SignRecognition | None = None

    @classmethod
    def build(cls, settings: Settings) -> Container:
        """Build container from settings, resolving all adapters."""
        event_bus = _build_event_bus(settings)
        llm = _build_llm(settings)
        embeddings = _build_embeddings(settings)
        stt, tts, image_describer, ocr = _build_media(settings)
        sign_recognition = _build_sign_recognition(settings)
        return cls(
            settings=settings,
            llm=llm,
            embeddings=embeddings,
            event_bus=event_bus,
            stt=stt,
            tts=tts,
            image_describer=image_describer,
            ocr=ocr,
            sign_recognition=sign_recognition,
        )


def _build_event_bus(settings: Settings) -> EventBus:
    """Build event bus: in-memory for dev, Redis for prod."""
    redis_url = settings.redis.url
    if redis_url and redis_url != "redis://localhost:6379/0":
        try:
            from ..adapters.events.redis_bus import RedisEventBus

            return RedisEventBus(redis_url=redis_url)
        except ImportError:
            pass

    from ..adapters.events.inmemory_bus import InMemoryEventBus

    return InMemoryEventBus()


def _build_llm(settings: Settings) -> ChatLLM:
    """Build LLM adapter based on provider setting."""
    provider = settings.llm.provider
    api_key = settings.llm.api_key or _resolve_api_key(settings, provider)
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


def _build_embeddings(settings: Settings) -> Embeddings | None:
    """Build embeddings adapter based on provider setting."""
    provider = settings.embedding.provider
    api_key = settings.embedding.api_key or _resolve_api_key(settings, provider)

    if not api_key:
        # No API key — return None (embeddings unavailable until configured)
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


def _build_media(settings: Settings) -> tuple[STT | Any, TTS | Any, ImageDescriber | Any, Any]:
    """Build media adapters (STT, TTS, ImageDescriber, OCR).

    Falls back to fake implementations when no API keys are configured
    or when the optional dependencies are not installed (ADR-051).
    """
    from ..adapters.media.fake_image_describer import FakeImageDescriber
    from ..adapters.media.fake_stt import FakeSTT
    from ..adapters.media.fake_tts import FakeTTS
    from ..adapters.media.ocr_processor import OCRProcessor

    # STT: prefer OpenAI cloud when key available, else Whisper local, else fake
    stt: Any
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
    tts: Any
    elevenlabs_key = getattr(settings, "elevenlabs_api_key", "")
    if elevenlabs_key:
        from ..adapters.media.elevenlabs_tts import ElevenLabsTTS

        tts = ElevenLabsTTS(api_key=elevenlabs_key)
    else:
        tts = FakeTTS()

    # Image describer: fake for now (real impl needs vision LLM, Sprint 9)
    image_describer = FakeImageDescriber()

    # OCR: always available (graceful degradation via lazy imports)
    ocr = OCRProcessor()

    return stt, tts, image_describer, ocr


def _build_sign_recognition(settings: Settings) -> SignRecognition:
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
            pass

    from ..adapters.media.fake_sign_recognition import FakeSignRecognition

    return FakeSignRecognition()


def _resolve_api_key(settings: Settings, provider: str) -> str:
    """Resolve API key from top-level settings based on provider."""
    mapping = {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "gemini": settings.google_api_key,
        "openrouter": settings.openrouter_api_key,
    }
    return mapping.get(provider, "")
