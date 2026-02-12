"""Fake TTS adapter for testing and CI.

Returns a minimal valid WAV file without calling any external API.
Used when no API keys are configured or in CI environments (ADR-051).
"""

from __future__ import annotations

import struct


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
        "<4sI4s"    # RIFF header
        "4sIHHIIHH"  # fmt chunk
        "4sI",       # data chunk header
        b"RIFF",
        36 + data_size,  # file size - 8
        b"WAVE",
        b"fmt ",
        16,              # fmt chunk size (PCM)
        1,               # audio format: PCM
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
