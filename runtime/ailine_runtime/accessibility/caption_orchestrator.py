"""Caption orchestrator for real-time Libras → Portuguese translation.

Manages per-session state: buffers incoming glosses, debounces rapid
updates, rate-limits LLM calls, and emits caption draft/final messages
via callback.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Coroutine
from typing import Any

import structlog

from ..ml.decoder import GlossBuffer
from .gloss_translator import GlossToTextTranslator

logger = structlog.get_logger(__name__)

# Message types emitted by the orchestrator
MSG_CAPTION_DRAFT = "caption_draft_delta"
MSG_CAPTION_FINAL = "caption_final_delta"


class CaptionOrchestrator:
    """Per-session orchestrator for Libras gloss → Portuguese caption pipeline.

    Receives gloss_partial and gloss_final messages from the frontend,
    debounces them, translates via LLM, and emits caption events.

    Rate limiting:
      - Maximum LLM calls per second (default 3 Hz)
      - Debounce window for partial updates (default 300ms)
    """

    def __init__(
        self,
        translator: GlossToTextTranslator,
        emit: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
        max_hz: float = 3.0,
        debounce_ms: int = 300,
        commit_threshold: float = 0.80,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            translator: The gloss-to-text translator.
            emit: Async callback to send messages to the client.
            max_hz: Maximum LLM translation calls per second.
            debounce_ms: Minimum interval between partial translations.
            commit_threshold: Confidence threshold for committing glosses.
        """
        self._translator = translator
        self._emit = emit
        self._min_interval = 1.0 / max_hz
        self._debounce_s = debounce_ms / 1000.0
        self._buffer = GlossBuffer(commit_threshold=commit_threshold)

        self._last_translate_time: float = 0.0
        self._pending_partial: list[str] | None = None
        self._debounce_task: asyncio.Task[None] | None = None
        self._committed_text: str = ""

    async def handle_message(self, message: dict[str, Any]) -> None:
        """Handle an incoming WebSocket message.

        Dispatches to the appropriate handler based on message type.
        """
        msg_type = message.get("type")
        if msg_type == "gloss_partial":
            await self._handle_partial(message)
        elif msg_type == "gloss_final":
            await self._handle_final(message)
        else:
            logger.warning("caption_orchestrator.unknown_type", type=msg_type)

    async def _handle_partial(self, message: dict[str, Any]) -> None:
        """Handle a gloss_partial message: debounce and translate."""
        glosses = message.get("glosses", [])
        confidence = message.get("confidence", 0.0)

        self._buffer.add_partial(glosses, confidence)
        self._pending_partial = glosses

        # Check for auto-committed glosses
        committed = self._buffer.commit()
        if committed:
            await self._translate_and_emit_final(committed)

        # Debounce partial translation
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        self._debounce_task = asyncio.create_task(self._debounced_translate_partial())

    async def _handle_final(self, message: dict[str, Any]) -> None:
        """Handle a gloss_final message: translate immediately."""
        glosses = message.get("glosses", [])
        confidence = message.get("confidence", 0.0)

        # Cancel any pending debounce
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()

        self._buffer.add_partial(glosses, confidence)
        # Force commit regardless of confidence
        committed = glosses if glosses else self._buffer.commit()
        self._buffer.reset()

        if committed:
            await self._translate_and_emit_final(committed)

    async def _debounced_translate_partial(self) -> None:
        """Wait for debounce interval, then translate partial glosses."""
        await asyncio.sleep(self._debounce_s)

        partial = self._buffer.get_partial()
        if not partial:
            return

        # Rate limit
        now = time.monotonic()
        elapsed = now - self._last_translate_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)

        self._last_translate_time = time.monotonic()

        try:
            translation = await self._translator.translate(partial)
            await self._emit(
                {
                    "type": MSG_CAPTION_DRAFT,
                    "text": translation,
                    "glosses": partial,
                    "confidence": self._buffer.partial_confidence,
                }
            )
        except Exception:
            logger.exception("caption_orchestrator.partial_translate_error")

    async def _translate_and_emit_final(self, glosses: list[str]) -> None:
        """Translate committed glosses and emit as final caption."""
        # Rate limit
        now = time.monotonic()
        elapsed = now - self._last_translate_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)

        self._last_translate_time = time.monotonic()

        try:
            translation = await self._translator.translate(glosses)
            separator = " " if self._committed_text else ""
            self._committed_text += separator + translation

            await self._emit(
                {
                    "type": MSG_CAPTION_FINAL,
                    "text": translation,
                    "full_text": self._committed_text,
                    "glosses": glosses,
                }
            )
        except Exception:
            logger.exception("caption_orchestrator.final_translate_error")

    def reset(self) -> None:
        """Reset session state."""
        self._buffer.reset()
        self._committed_text = ""
        self._pending_partial = None
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
