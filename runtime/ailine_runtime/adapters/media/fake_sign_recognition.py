"""Fake sign recognition adapter for testing and CI.

Returns deterministic gesture predictions without calling any external model.
Used when no model is configured or in CI environments (ADR-051).
Supports the ``SignRecognition`` protocol from ``domain.ports.media``.
"""

from __future__ import annotations

from typing import ClassVar

# Canonical set of supported Libras gestures for MVP (ADR-026).
_MVP_GESTURES = ["oi", "obrigado", "sim", "nao"]


class FakeSignRecognition:
    """Sign recognition implementation that returns canned predictions for testing.

    Satisfies the ``SignRecognition`` protocol from ``domain.ports.media``.

    The gesture is selected deterministically based on the input byte length
    so that tests are reproducible.  An optional ``responses`` parameter lets
    callers inject a specific sequence of gesture strings that will cycle.
    """

    GESTURES: ClassVar[list[str]] = list(_MVP_GESTURES)

    def __init__(
        self,
        *,
        responses: list[dict] | None = None,
        confidence: float = 0.95,
    ) -> None:
        self._responses = responses
        self._confidence = confidence
        self._call_count = 0

    async def recognize(self, video_bytes: bytes) -> dict:
        """Return a deterministic fake recognition result.

        If custom ``responses`` were provided at construction, they are
        cycled through.  Otherwise a gesture is selected based on the
        length of the input bytes modulo the number of gestures.
        """
        if self._responses:
            result = self._responses[self._call_count % len(self._responses)]
            self._call_count += 1
            return result

        gesture_idx = len(video_bytes) % len(self.GESTURES)
        self._call_count += 1
        return {
            "gesture": self.GESTURES[gesture_idx],
            "confidence": self._confidence,
            "landmarks": [],
            "model": "fake",
        }
