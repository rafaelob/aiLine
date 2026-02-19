"""Lightweight DI container — built once at startup, immutable during requests.

Contains the Container dataclass with health-check, validation, and lifecycle
methods. Adapter factory functions live in container_adapters.py.
"""

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
    ImageGenerator,
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
        ``stt``, ``tts``, ``image_describer``, ``image_generator``, ``ocr``,
        ``sign_recognition``) default to None or fake adapters (ADR-051).
        Callers must check for None before using optional adapters.
        The ``close()`` method is idempotent and safe to call multiple times;
        it logs but does not raise on cleanup errors, ensuring all resources
        are attempted.
    """

    settings: Settings

    # Resolved port implementations (populated by build())
    llm: ChatLLM | None = None
    embeddings: Embeddings | None = None
    vectorstore: VectorStore | None = None
    event_bus: EventBus | None = None

    # Media adapters (STT, TTS, image description/generation, OCR, sign recognition)
    stt: STT | None = None
    tts: TTS | None = None
    image_describer: ImageDescriber | None = None
    image_generator: ImageGenerator | None = None
    ocr: OCRProcessor | None = None
    sign_recognition: SignRecognition | None = None

    # Internal: holds references to resources that need cleanup on shutdown.
    # Using a mutable list inside a frozen dataclass is safe because the list
    # reference itself is never reassigned -- only its contents change.
    _cleanup: list[Any] = field(default_factory=list, repr=False)

    @classmethod
    def build(cls, settings: Settings) -> Container:
        """Build container from settings, resolving all adapters."""
        from .container_adapters import (
            build_embeddings,
            build_event_bus,
            build_image_generator,
            build_llm,
            build_media,
            build_sign_recognition,
            build_vectorstore,
        )

        cleanup: list[Any] = []
        event_bus = build_event_bus(settings)
        llm = build_llm(settings)
        embeddings = build_embeddings(settings)
        vectorstore = build_vectorstore(settings, cleanup)
        stt, tts, image_describer, ocr = build_media(settings)
        sign_recognition = build_sign_recognition(settings)
        image_generator = build_image_generator(settings)
        container = cls(
            settings=settings,
            llm=llm,
            embeddings=embeddings,
            vectorstore=vectorstore,
            event_bus=event_bus,
            stt=stt,
            tts=tts,
            image_describer=image_describer,
            image_generator=image_generator,
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

        # Redis / event bus connectivity via public protocol method
        if self.event_bus is not None:
            try:
                reachable = await self.event_bus.ping()
                result["redis"] = {"status": "ok" if reachable else "unreachable"}
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
                f"Container validation failed in production: missing critical ports: {', '.join(missing_critical)}"
            )

        # Optional ports -- degraded operation when missing.
        optional_checks: list[tuple[str, Any, str]] = [
            ("vectorstore", self.vectorstore, "vector search unavailable"),
            ("embeddings", self.embeddings, "embedding generation unavailable"),
            ("stt", self.stt, "speech-to-text unavailable"),
            ("tts", self.tts, "text-to-speech unavailable"),
            ("image_describer", self.image_describer, "image description unavailable"),
            ("image_generator", self.image_generator, "image generation unavailable"),
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
            ("image_generator", self.image_generator),
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
