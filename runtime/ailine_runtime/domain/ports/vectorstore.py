"""Port: vector stores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class VectorSearchResult:
    """Single result from a vector similarity search."""

    id: str
    score: float
    text: str
    metadata: dict[str, Any]


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector stores."""

    async def upsert(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, Any]],
        tenant_id: str | None = None,
    ) -> None: ...

    async def search(
        self,
        *,
        query_embedding: list[float],
        k: int = 5,
        filters: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> list[VectorSearchResult]: ...

    async def delete(self, *, ids: list[str]) -> None: ...
