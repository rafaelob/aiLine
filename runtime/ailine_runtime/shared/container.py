from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, NamedTuple

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


class ValidationResult(NamedTuple):
    """Structured result from container validation.

    Attributes:
        ok: True when all critical ports are wired (no missing required adapters).
        missing_critical: Names of required ports that are None.
        missing_optional: Names of optional ports that are None (informational).
    """

    ok: bool
    missing_critical: list[str]
    missing_optional: list[str]


@dataclass(frozen=True)
class Container:
    """Lightweight DI container. Built once at startup, immutable during requests.

    Lifecycle: ``build(settings)`` -> ``validate()`` -> use -> ``close()``.

    The container is a frozen dataclass, so fields cannot be mutated after
    construction.  Mutable cleanup state (engine references for graceful
    shutdown) is stored in the ``_cleanup`` list using ``field(default_factory)``,
    which is itself immutable at the reference level but its *contents* can
    be mutated (append/pop) -- a deliberate pattern to combine immutability
    of the public API with lifecycle management.

    Graceful degradation:
        Required ports (``llm``, ``event_bus``) must be present in production
        (validated at startup). Optional ports (``vectorstore``, ``embeddings``,
        ``stt``, ``tts``, ``image_describer``, ``ocr``, ``sign_recognition``)
        default to None or fake adapters (ADR-051). Callers must check for
        None before using optional adapters. The ``close()`` method is
        idempotent and safe to call multiple times; it logs but does not
        raise on cleanup errors, ensuring all resources are attempted.
    """

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
    ocr: OCRProcessor | None = None
    sign_recognition: SignRecognition | None = None

    # Internal: holds references to resources that need cleanup on shutdown.
    # Using a mutable list inside a frozen dataclass is safe because the list
    # reference itself is never reassigned -- only its contents change.
    _cleanup: list[Any] = field(default_factory=list, repr=False)

    @classmethod
    def build(cls, settings: Settings) -> Container:
        """Build container from settings, resolving all adapters."""
        cleanup: list[Any] = []
        event_bus = _build_event_bus(settings)
        llm = _build_llm(settings)
        embeddings = _build_embeddings(settings)
        vectorstore = _build_vectorstore(settings, cleanup)
        stt, tts, image_describer, ocr = _build_media(settings)
        sign_recognition = _build_sign_recognition(settings)
        container = cls(
            settings=settings,
            llm=llm,
            embeddings=embeddings,
            vectorstore=vectorstore,
            event_bus=event_bus,
            stt=stt,
            tts=tts,
            image_describer=image_describer,
            ocr=ocr,
            sign_recognition=sign_recognition,
            _cleanup=cleanup,
        )
        container.validate()
        return container

    # -- Scalability: health check & pool stats --------------------------------

    async def health_check(self) -> dict[str, Any]:
        """Verify connectivity to DB and Redis, return pool statistics.

        Returns a dict with keys:
            - ``db``: ``{"status": "ok"|"unavailable"|"error", ...pool stats}``
            - ``redis``: ``{"status": "ok"|"unavailable"|"error"}``
        """
        result: dict[str, Any] = {
            "db": {"status": "unavailable"},
            "redis": {"status": "unavailable"},
        }

        # DB pool stats
        for item in self._cleanup:
            if hasattr(item, "pool"):
                pool = item.pool
                try:
                    result["db"] = {
                        "status": "ok",
                        "pool_size": pool.size(),
                        "checked_in": pool.checkedin(),
                        "checked_out": pool.checkedout(),
                        "overflow": pool.overflow(),
                    }
                except Exception as exc:
                    result["db"] = {"status": "error", "detail": str(exc)}
                break

        # Redis connectivity
        if self.event_bus is not None and hasattr(self.event_bus, "_redis"):
            try:
                redis_client = self.event_bus._redis
                await redis_client.ping()
                result["redis"] = {"status": "ok"}
            except Exception as exc:
                result["redis"] = {"status": "error", "detail": str(exc)}

        return result

    # -- Scalability: graceful shutdown ----------------------------------------

    async def close(self) -> None:
        """Dispose SQLAlchemy engine pools and close Redis connections.

        Safe to call multiple times.  Logs errors but does not raise,
        ensuring all resources are attempted for cleanup.
        """
        # Dispose SQLAlchemy engines
        for item in self._cleanup:
            try:
                await item.dispose()
                _log.info("container.engine_disposed")
            except Exception:
                _log.exception("container.engine_dispose_failed")

        # Close Redis event bus
        if self.event_bus is not None and hasattr(self.event_bus, "close"):
            try:
                await self.event_bus.close()
                _log.info("container.event_bus_closed")
            except Exception:
                _log.exception("container.event_bus_close_failed")

    # -- DI: container validation ----------------------------------------------

    def validate(self) -> ValidationResult:
        """Validate that critical ports are wired correctly.

        Checks all required ports (llm, event_bus) and logs warnings for
        missing optional adapters. Returns a ``ValidationResult`` with
        structured information about what is missing.

        In production mode (``settings.env == "production"``), raises
        ``ValueError`` if any critical port is None.

        Returns:
            A ``ValidationResult`` where ``ok`` is True when all critical
            ports are present.
        """
        env = self.settings.env
        missing_critical: list[str] = []
        missing_optional: list[str] = []

        # Required ports -- must be present for the system to function.
        if self.llm is None:
            missing_critical.append("llm")
        if self.event_bus is None:
            missing_critical.append("event_bus")

        if env == "production" and missing_critical:
            raise ValueError(
                f"Container validation failed in production: "
                f"missing critical ports: {', '.join(missing_critical)}"
            )

        # Optional ports -- degraded operation when missing.
        optional_checks: list[tuple[str, Any, str]] = [
            ("vectorstore", self.vectorstore, "vector search unavailable"),
            ("embeddings", self.embeddings, "embedding generation unavailable"),
            ("stt", self.stt, "speech-to-text unavailable"),
            ("tts", self.tts, "text-to-speech unavailable"),
            ("image_describer", self.image_describer, "image description unavailable"),
            ("ocr", self.ocr, "OCR text extraction unavailable"),
            ("sign_recognition", self.sign_recognition, "sign recognition unavailable"),
        ]
        for name, value, description in optional_checks:
            if value is None:
                missing_optional.append(name)
                _log.warning(
                    "container.missing_optional_adapter: %s is None (%s)",
                    name,
                    description,
                )

        ok = len(missing_critical) == 0
        result = ValidationResult(
            ok=ok,
            missing_critical=missing_critical,
            missing_optional=missing_optional,
        )

        if ok:
            _log.info(
                "container.validation_passed missing_optional=%d",
                len(missing_optional),
            )
        else:
            _log.warning(
                "container.validation_degraded missing_critical=%s",
                ", ".join(missing_critical),
            )

        return result

    # -- Debugging: repr -------------------------------------------------------

    def __repr__(self) -> str:
        """Show which adapters are active vs None for debugging."""
        fields = [
            ("llm", self.llm),
            ("embeddings", self.embeddings),
            ("vectorstore", self.vectorstore),
            ("event_bus", self.event_bus),
            ("stt", self.stt),
            ("tts", self.tts),
            ("image_describer", self.image_describer),
            ("ocr", self.ocr),
            ("sign_recognition", self.sign_recognition),
        ]
        parts = []
        for name, value in fields:
            if value is None:
                parts.append(f"{name}=None")
            else:
                parts.append(f"{name}={type(value).__name__}")
        return f"Container(env={self.settings.env!r}, {', '.join(parts)})"


def _build_vectorstore(
    settings: Settings, cleanup: list[Any]
) -> VectorStore | None:
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


def _build_event_bus(settings: Settings) -> EventBus:
    """Build event bus: in-memory for dev, Redis for prod.

    Uses AILINE_EVENT_BUS_PROVIDER setting (redis|inmemory) when set,
    otherwise falls back to detecting a non-empty redis URL.
    """
    import os

    explicit_provider = os.getenv("AILINE_EVENT_BUS_PROVIDER", "").lower()
    redis_url = settings.redis.url

    use_redis = (
        explicit_provider == "redis"
        or (explicit_provider == "" and bool(redis_url))
    )

    if use_redis and redis_url:
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


def _build_media(
    settings: Settings,
) -> tuple[STT | Any, TTS | Any, ImageDescriber | Any, OCRProcessor]:
    """Build media adapters (STT, TTS, ImageDescriber, OCR).

    Falls back to fake implementations when no API keys are configured
    or when the optional dependencies are not installed (ADR-051).
    """
    from ..adapters.media.fake_image_describer import FakeImageDescriber
    from ..adapters.media.fake_stt import FakeSTT
    from ..adapters.media.fake_tts import FakeTTS
    from ..adapters.media.ocr_processor import OCRProcessor as OCRProcessorAdapter

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
    ocr = OCRProcessorAdapter()

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
