"""Fake STT adapter for testing and CI.

Returns deterministic transcription strings without calling any external API.
Used when no API keys are configured or in CI environments (ADR-051).
"""

from __future__ import annotations


class FakeSTT:
    """STT implementation that returns canned transcriptions for testing.

    Satisfies the ``STT`` protocol from ``domain.ports.media``.
    """

    def __init__(self, *, responses: list[str] | None = None) -> None:
        self._responses = responses or []
        self._call_count = 0

    async def transcribe(
        self, audio_bytes: bytes, *, language: str = "pt"
    ) -> str:
        """Return a deterministic transcription.

        If custom responses were provided at construction, they are
        cycled through.  Otherwise a descriptive placeholder is returned.
        """
        if self._responses:
            text = self._responses[self._call_count % len(self._responses)]
        else:
            text = (
                f"[Transcricao simulada: {len(audio_bytes)} bytes "
                f"de audio em {language}]"
            )
        self._call_count += 1
        return text
