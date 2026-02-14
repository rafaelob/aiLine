"""In-memory VectorStore adapter for testing.

Stores vectors in a plain dictionary and computes cosine similarity
using NumPy.  No external dependencies beyond NumPy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ...domain.ports.vectorstore import VectorSearchResult


@dataclass
class _StoredChunk:
    """Internal representation of a stored chunk."""

    id: str
    embedding: np.ndarray
    text: str
    metadata: dict[str, Any]
    tenant_id: str = ""


class InMemoryVectorStore:
    """VectorStore backed by an in-memory dictionary.

    Suitable for unit tests and lightweight integration tests that need
    deterministic, fast vector operations without external infrastructure.
    """

    def __init__(self) -> None:
        self._store: dict[str, _StoredChunk] = {}

    # -- Inspection helpers (test-only) ---------------------------------------

    @property
    def count(self) -> int:
        """Number of stored chunks."""
        return len(self._store)

    def clear(self) -> None:
        """Remove all stored chunks."""
        self._store.clear()

    # -- Protocol methods -----------------------------------------------------

    async def upsert(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, Any]],
        tenant_id: str | None = None,
    ) -> None:
        """Insert or update chunks in memory."""
        for i, doc_id in enumerate(ids):
            self._store[doc_id] = _StoredChunk(
                id=doc_id,
                embedding=np.array(embeddings[i], dtype=np.float32),
                text=texts[i],
                metadata=dict(metadatas[i]),
                tenant_id=tenant_id or "",
            )

    async def search(
        self,
        *,
        query_embedding: list[float],
        k: int = 5,
        filters: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> list[VectorSearchResult]:
        """Find the *k* most similar chunks by cosine similarity.

        Args:
            query_embedding: The query vector.
            k: Maximum number of results.
            filters: Optional metadata key-value equality filters.
            tenant_id: When provided, only chunks belonging to this
                tenant are considered (structural isolation).

        Returns:
            Results ordered by descending similarity score.
        """
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = float(np.linalg.norm(query_vec))
        if query_norm == 0:
            return []

        scored: list[tuple[float, _StoredChunk]] = []

        for chunk in self._store.values():
            # Structural tenant isolation
            if tenant_id is not None and chunk.tenant_id != tenant_id:
                continue

            # Apply metadata filters
            if filters and not _matches_filters(chunk.metadata, filters):
                continue

            chunk_norm = float(np.linalg.norm(chunk.embedding))
            if chunk_norm == 0:
                continue

            similarity = float(np.dot(query_vec, chunk.embedding) / (query_norm * chunk_norm))
            scored.append((similarity, chunk))

        # Sort by descending similarity
        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [
            VectorSearchResult(
                id=chunk.id,
                score=score,
                text=chunk.text,
                metadata=dict(chunk.metadata),
            )
            for score, chunk in scored[:k]
        ]

    async def delete(self, *, ids: list[str]) -> None:
        """Delete chunks by their IDs."""
        for doc_id in ids:
            self._store.pop(doc_id, None)


def _matches_filters(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
    """Check whether *metadata* satisfies all equality *filters*."""
    return all(key in metadata and metadata[key] == value for key, value in filters.items())
