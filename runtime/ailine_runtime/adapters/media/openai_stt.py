"""OpenAI cloud STT adapter using gpt-4o-transcribe.

Provides high-quality cloud-based speech-to-text via the OpenAI
Transcriptions API.  Preferred when local GPU is unavailable and
latency budget allows a network round-trip (ADR-011).

Pricing: gpt-4o-transcribe $0.006/min, gpt-4o-mini-transcribe $0.003/min.
Requires: ``openai>=2.11`` (pinned in pyproject.toml[media]).
"""

from __future__ import annotations

import io
from typing import Any


class OpenAISTT:
    """STT using OpenAI's gpt-4o-transcribe API.

    Satisfies the ``STT`` protocol from ``domain.ports.media``.

    Parameters
    ----------
    api_key:
        OpenAI API key.  If empty, the ``AsyncOpenAI`` client will
        fall back to the ``OPENAI_API_KEY`` environment variable.
    model:
        Transcription model identifier.
    """

    def __init__(
        self,
        *,
        api_key: str = "",
        model: str = "gpt-4o-transcribe",
    ) -> None:
        self._model = model
        self._client: Any = None
        self._api_key = api_key

    def _ensure_client(self) -> None:
        """Lazy-initialise the async OpenAI client."""
        if self._client is not None:
            return
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ImportError(
                "openai is required for OpenAISTT. "
                "Install with: pip install 'openai>=2.11'"
            ) from exc
        if self._api_key:
            self._client = AsyncOpenAI(api_key=self._api_key)
        else:
            self._client = AsyncOpenAI()

    async def transcribe(
        self, audio_bytes: bytes, *, language: str = "pt"
    ) -> str:
        """Transcribe audio bytes via the OpenAI Transcriptions API."""
        self._ensure_client()
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"  # type: ignore[attr-defined]
        response = await self._client.audio.transcriptions.create(
            model=self._model,
            file=audio_file,
            language=language,
        )
        return response.text
