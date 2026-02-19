"""Fake TTS adapter for testing and CI.

Returns a minimal valid WAV file without calling any external API.
Used when no API keys are configured or in CI environments (ADR-051).

Satisfies the ``TTS`` protocol from ``domain.ports.media``.
"""

from __future__ import annotations

import struct

from ...domain.ports.media import VoiceInfo

# Pre-built voice catalog for deterministic testing.
_FAKE_VOICES = [
    VoiceInfo(
        id="fake-voice-en-female",
        name="Aria (Fake)",
        language="en",
        gender="female",
        preview_url="",
        labels={"accent": "american", "use_case": "narration"},
    ),
    VoiceInfo(
        id="fake-voice-en-male",
        name="Marcus (Fake)",
        language="en",
        gender="male",
        preview_url="",
        labels={"accent": "british", "use_case": "narration"},
    ),
    VoiceInfo(
        id="fake-voice-pt-female",
        name="Clara (Fake)",
        language="pt-BR",
        gender="female",
        preview_url="",
        labels={"accent": "brazilian", "use_case": "narration"},
    ),
    VoiceInfo(
        id="fake-voice-es-male",
        name="Diego (Fake)",
        language="es",
        gender="male",
        preview_url="",
        labels={"accent": "castilian", "use_case": "narration"},
    ),
]


def _create_silent_wav(*, duration_ms: int = 100, sample_rate: int = 16000) -> bytes:
    """Build a minimal valid WAV file containing silence.

    The file uses 16-bit mono PCM at the given sample rate.
    This is enough for downstream consumers that validate the WAV header
    (e.g. audio players, STT round-trip tests).
    """
    num_channels = 1
    bits_per_sample = 16
    bytes_per_sample = bits_per_sample // 8
    num_samples = int(sample_rate * duration_ms / 1000)
    data_size = num_samples * num_channels * bytes_per_sample
    byte_rate = sample_rate * num_channels * bytes_per_sample
    block_align = num_channels * bytes_per_sample

    header = struct.pack(
        "<4sI4s"  # RIFF header
        "4sIHHIIHH"  # fmt chunk
        "4sI",  # data chunk header
        b"RIFF",
        36 + data_size,  # file size - 8
        b"WAVE",
        b"fmt ",
        16,  # fmt chunk size (PCM)
        1,  # audio format: PCM
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    # Silence = zero bytes
    return header + b"\x00" * data_size


class FakeTTS:
    """TTS implementation that returns a valid silent WAV for testing.

    Satisfies the ``TTS`` protocol from ``domain.ports.media``.
    """

    def __init__(self, *, duration_ms: int = 100) -> None:
        self._duration_ms = duration_ms

    async def synthesize(
        self, text: str, *, locale: str = "pt-BR", speed: float = 1.0
    ) -> bytes:
        """Return a minimal valid WAV file containing silence."""
        return _create_silent_wav(duration_ms=self._duration_ms)

    async def list_voices(
        self, *, language: str | None = None
    ) -> list[VoiceInfo]:
        """Return a static list of fake voices, optionally filtered by language."""
        if language:
            lang_lower = language.lower()
            return [
                v for v in _FAKE_VOICES if lang_lower in v.language.lower()
            ]
        return list(_FAKE_VOICES)

    async def get_voice(self, voice_id: str) -> VoiceInfo | None:
        """Return a fake voice by ID, or None if not found."""
        for v in _FAKE_VOICES:
            if v.id == voice_id:
                return v
        return None
