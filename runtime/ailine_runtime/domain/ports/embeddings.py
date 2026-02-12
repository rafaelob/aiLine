"""Port: embedding providers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Embeddings(Protocol):
    """Protocol for embedding providers."""

    @property
    def dimensions(self) -> int: ...

    @property
    def model_name(self) -> str: ...

    async def embed_text(self, text: str) -> list[float]: ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
