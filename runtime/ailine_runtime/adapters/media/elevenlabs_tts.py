"""ElevenLabs TTS adapter (primary cloud TTS).

Provides high-quality multilingual text-to-speech via the ElevenLabs
REST API using the ``eleven_multilingual_v2`` model (ADR-021).

Requires: ``httpx>=0.28`` (already a core dependency).
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

_ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"


class ElevenLabsTTS:
    """TTS using ElevenLabs API (primary).

    Satisfies the ``TTS`` protocol from ``domain.ports.media``.

    Parameters
    ----------
    api_key:
        ElevenLabs API key.  Required for production use.
    voice_id:
        Target voice identifier.
    model_id:
        ElevenLabs model.  ``eleven_multilingual_v2`` supports PT-BR.
    """

    def __init__(
        self,
        *,
        api_key: str = "",
        voice_id: str = "default",
        model_id: str = "eleven_multilingual_v2",
    ) -> None:
        self._api_key = api_key
        self._voice_id = voice_id
        self._model_id = model_id

    async def synthesize(
        self, text: str, *, locale: str = "pt-BR", speed: float = 1.0
    ) -> bytes:
        """Synthesize text to audio bytes via ElevenLabs API.

        Returns raw audio bytes (mpeg by default from ElevenLabs).

        Raises
        ------
        httpx.HTTPStatusError
            On non-2xx responses from the API.
        ImportError
            If httpx is not installed (should not happen as it is a
            core dependency).
        """
        import httpx

        url = f"{_ELEVENLABS_API_BASE}/text-to-speech/{self._voice_id}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self._model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.debug(
                "elevenlabs_tts.request",
                voice_id=self._voice_id,
                model_id=self._model_id,
                text_length=len(text),
                locale=locale,
            )
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.debug(
                "elevenlabs_tts.response",
                status=response.status_code,
                content_length=len(response.content),
            )
            return response.content
