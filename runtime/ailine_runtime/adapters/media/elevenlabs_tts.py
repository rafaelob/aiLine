"""ElevenLabs TTS adapter (primary cloud TTS).

Provides high-quality multilingual text-to-speech via the ElevenLabs
REST API using the ``eleven_v3`` model.

Requires: ``httpx>=0.28`` (already a core dependency).

Satisfies the ``TTS`` protocol from ``domain.ports.media``.
"""

from __future__ import annotations

import structlog

from ...domain.ports.media import VoiceInfo

logger = structlog.get_logger(__name__)

_ELEVENLABS_API_BASE = "https://api.elevenlabs.io/v1"

# Default voice settings for consistent, natural-sounding output.
_DEFAULT_VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75,
}


class ElevenLabsTTS:
    """TTS using ElevenLabs API (primary).

    Satisfies the ``TTS`` protocol from ``domain.ports.media``.

    Parameters
    ----------
    api_key:
        ElevenLabs API key.  Required for production use.
    voice_id:
        Default voice identifier used when callers do not specify one.
    model_id:
        ElevenLabs model.  ``eleven_v3`` is the latest multilingual model.
    timeout:
        HTTP request timeout in seconds.
    """

    def __init__(
        self,
        *,
        api_key: str = "",
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        model_id: str = "eleven_v3",
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._voice_id = voice_id
        self._model_id = model_id
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }

    async def synthesize(
        self, text: str, *, locale: str = "pt-BR", speed: float = 1.0
    ) -> bytes:
        """Synthesize text to audio bytes via ElevenLabs API.

        Returns raw audio bytes (mpeg by default from ElevenLabs).

        Raises
        ------
        httpx.HTTPStatusError
            On non-2xx responses from the API.
        """
        import httpx

        url = f"{_ELEVENLABS_API_BASE}/text-to-speech/{self._voice_id}"
        payload = {
            "text": text,
            "model_id": self._model_id,
            "voice_settings": _DEFAULT_VOICE_SETTINGS,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            logger.debug(
                "elevenlabs_tts.synthesize",
                voice_id=self._voice_id,
                model_id=self._model_id,
                text_length=len(text),
                locale=locale,
            )
            response = await client.post(
                url, headers=self._headers(), json=payload
            )
            response.raise_for_status()
            logger.debug(
                "elevenlabs_tts.synthesize_ok",
                status=response.status_code,
                content_length=len(response.content),
            )
            return response.content

    async def list_voices(
        self, *, language: str | None = None
    ) -> list[VoiceInfo]:
        """Fetch available voices from ElevenLabs.

        When *language* is provided, filters to voices whose labels
        contain a matching language tag (case-insensitive substring).
        """
        import httpx

        url = f"{_ELEVENLABS_API_BASE}/voices"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            logger.debug("elevenlabs_tts.list_voices", language=language)
            response = await client.get(
                url,
                headers={"xi-api-key": self._api_key},
            )
            response.raise_for_status()

        data = response.json()
        voices_raw = data.get("voices", [])
        voices: list[VoiceInfo] = []

        for v in voices_raw:
            labels = v.get("labels", {}) or {}
            # Normalize labels to str->str
            str_labels = {str(k): str(val) for k, val in labels.items()}
            voice_lang = str_labels.get("language", "en")
            gender = str_labels.get("gender", "neutral")

            vi = VoiceInfo(
                id=v.get("voice_id", ""),
                name=v.get("name", ""),
                language=voice_lang,
                gender=gender,
                preview_url=v.get("preview_url", ""),
                labels=str_labels,
            )
            voices.append(vi)

        if language:
            lang_lower = language.lower()
            voices = [
                v
                for v in voices
                if lang_lower in v.language.lower()
                or any(lang_lower in val.lower() for val in v.labels.values())
            ]

        logger.debug(
            "elevenlabs_tts.list_voices_ok",
            total=len(voices_raw),
            filtered=len(voices),
        )
        return voices

    async def get_voice(self, voice_id: str) -> VoiceInfo | None:
        """Fetch details for a single voice by ID.

        Returns None if the voice is not found (404).
        """
        import httpx

        url = f"{_ELEVENLABS_API_BASE}/voices/{voice_id}"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            logger.debug("elevenlabs_tts.get_voice", voice_id=voice_id)
            response = await client.get(
                url,
                headers={"xi-api-key": self._api_key},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()

        v = response.json()
        labels = v.get("labels", {}) or {}
        str_labels = {str(k): str(val) for k, val in labels.items()}

        return VoiceInfo(
            id=v.get("voice_id", voice_id),
            name=v.get("name", ""),
            language=str_labels.get("language", "en"),
            gender=str_labels.get("gender", "neutral"),
            preview_url=v.get("preview_url", ""),
            labels=str_labels,
        )
