"""Fake ImageGenerator adapter for testing and CI.

Returns a deterministic 1x1 transparent PNG without calling any external API.
Satisfies the ``ImageGenerator`` protocol from ``domain.ports.media``.
"""

from __future__ import annotations

# Minimal valid 1x1 transparent PNG (67 bytes).
_TRANSPARENT_1X1_PNG = (
    b"\x89PNG\r\n\x1a\n"  # PNG signature
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"  # 1x1 RGBA
    b"\x00\x00\x00\nIDATx"
    b"\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeImageGenerator:
    """ImageGenerator that returns a tiny transparent PNG.

    Useful for unit tests and CI where no real image generation is needed.
    """

    def __init__(self) -> None:
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    async def generate(
        self,
        prompt: str,
        *,
        aspect_ratio: str = "16:9",
        style: str = "educational_illustration",
        size: str = "1K",
    ) -> bytes:
        """Return a 1x1 transparent PNG."""
        self._call_count += 1
        return _TRANSPARENT_1X1_PNG
