"""Fake ImageDescriber adapter for testing and CI.

Returns a deterministic image description without calling any external API.
"""

from __future__ import annotations


class FakeImageDescriber:
    """ImageDescriber implementation that returns canned descriptions.

    Satisfies the ``ImageDescriber`` protocol from ``domain.ports.media``.
    """

    def __init__(self, *, responses: list[str] | None = None) -> None:
        self._responses = responses or []
        self._call_count = 0

    async def describe(
        self, image_bytes: bytes, *, locale: str = "pt-BR"
    ) -> str:
        """Return a deterministic image description."""
        if self._responses:
            text = self._responses[self._call_count % len(self._responses)]
        else:
            text = f"[Descricao simulada: imagem de {len(image_bytes)} bytes]"
        self._call_count += 1
        return text
