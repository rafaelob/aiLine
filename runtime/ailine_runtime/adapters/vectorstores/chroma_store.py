"""ChromaDB VectorStore adapter for local development.

Provides a lightweight, file- or in-memory-based vector store that does
not require PostgreSQL.  Useful for rapid local iteration and demos.
"""

from __future__ import annotations

from typing import Any

from ...domain.ports.vectorstore import VectorSearchResult
from ...shared.observability import get_logger

_log = get_logger("ailine.adapters.vectorstores.chroma")


class ChromaVectorStore:
    """VectorStore backed by ChromaDB.

    Args:
        collection_name: Name of the Chroma collection.
        persist_directory: Path to persist on disk.  ``None`` for
            ephemeral (in-memory) mode.
    """

    def __init__(
        self,
        *,
        collection_name: str = "chunks",
        persist_directory: str | None = None,
    ) -> None:
        import chromadb

        if persist_directory:
            self._client = chromadb.PersistentClient(path=persist_directory)
        else:
            self._client = chromadb.EphemeralClient()

        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        _log.info(
            "chroma_store_init",
            collection=collection_name,
            persist=persist_directory,
        )

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
        """Insert or update documents in the Chroma collection.

        ChromaDB's ``upsert`` is synchronous; we call it directly since
        the library does not expose an async API.
        """
        if not ids:
            return

        _log.debug("upsert", collection=self._collection.name, count=len(ids))

        # ChromaDB requires metadata values to be str, int, float, or bool.
        # Serialize any nested structures.
        # Inject tenant_id into metadata for structural isolation (ADR-060)
        enriched_metas = metadatas
        if tenant_id is not None:
            enriched_metas = [{**m, "_tenant_id": tenant_id} for m in metadatas]
        sanitized_metas = [_sanitize_metadata(m) for m in enriched_metas]

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=sanitized_metas,
        )

    async def search(
        self,
        *,
        query_embedding: list[float],
        k: int = 5,
        filters: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> list[VectorSearchResult]:
        """Query the Chroma collection for similar vectors.

        Chroma returns distances; for cosine space, distance = 1 - similarity,
        so we convert back to a similarity score.

        Args:
            query_embedding: The query vector.
            k: Maximum number of results.
            filters: Optional metadata filters passed as Chroma ``where`` clause.

        Returns:
            List of ``VectorSearchResult`` ordered by descending similarity.
        """
        _log.debug("search", k=k, filters=filters, tenant_id=tenant_id)

        # Structural tenant isolation via Chroma where clause (ADR-060)
        where = dict(filters) if filters else {}
        if tenant_id is not None:
            where["_tenant_id"] = tenant_id
        where_clause: dict[str, Any] | None = where or None

        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_clause,
            include=["documents", "metadatas", "distances"],
        )

        items: list[VectorSearchResult] = []
        if result["ids"] and result["ids"][0]:
            for i, doc_id in enumerate(result["ids"][0]):
                distance = result["distances"][0][i] if result["distances"] else 0.0
                score = 1.0 - distance  # cosine distance -> similarity
                text = result["documents"][0][i] if result["documents"] else ""
                metadata = result["metadatas"][0][i] if result["metadatas"] else {}
                items.append(
                    VectorSearchResult(
                        id=doc_id,
                        score=score,
                        text=text,
                        metadata=metadata,
                    )
                )

        return items

    async def delete(self, *, ids: list[str]) -> None:
        """Delete documents by their IDs."""
        if not ids:
            return

        _log.debug("delete", collection=self._collection.name, count=len(ids))
        self._collection.delete(ids=ids)


def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Flatten metadata values to types Chroma accepts."""
    import json

    sanitized: dict[str, str | int | float | bool] = {}
    for key, value in meta.items():
        if isinstance(value, str | int | float | bool):
            sanitized[key] = value
        else:
            sanitized[key] = json.dumps(value, ensure_ascii=False, default=str)
    return sanitized
