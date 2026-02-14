"""RAG (Retrieval-Augmented Generation) query service.

Embeds a user query, searches the vector store with optional metadata
filters, and returns ranked results above a configurable similarity
threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...domain.ports.embeddings import Embeddings
from ...domain.ports.vectorstore import VectorSearchResult, VectorStore
from ...shared.observability import get_logger

_log = get_logger("ailine.app.services.rag")

DEFAULT_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.7


@dataclass(frozen=True)
class RAGResult:
    """Container for a completed RAG query.

    Attributes:
        query: The original query text.
        results: Ranked search results above the similarity threshold.
        total_candidates: How many results the vector store returned
            before threshold filtering.
    """

    query: str
    results: list[VectorSearchResult]
    total_candidates: int


class RAGService:
    """Retrieval-Augmented Generation query service.

    Orchestrates:
    1. Embed the query text.
    2. Search the vector store with optional metadata filters.
    3. Filter results below the similarity threshold.
    4. Return ranked results with source attribution.

    Args:
        embeddings: An adapter satisfying the ``Embeddings`` protocol.
        vector_store: An adapter satisfying the ``VectorStore`` protocol.
        default_k: Default number of candidates to retrieve from the
            vector store before threshold filtering.
        similarity_threshold: Minimum similarity score to include a result.
    """

    def __init__(
        self,
        *,
        embeddings: Embeddings,
        vector_store: VectorStore,
        default_k: int = DEFAULT_K,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> None:
        self._embeddings = embeddings
        self._store = vector_store
        self._default_k = default_k
        self._threshold = similarity_threshold

    async def query(
        self,
        *,
        text: str,
        k: int | None = None,
        filters: dict[str, Any] | None = None,
        similarity_threshold: float | None = None,
        tenant_id: str | None = None,
    ) -> RAGResult:
        """Execute a RAG retrieval query.

        Args:
            text: The query text to embed and search with.
            k: Override the default number of candidates.
            filters: Optional metadata filters (e.g., ``teacher_id``,
                ``subject``) passed to the vector store.
            similarity_threshold: Override the default similarity threshold.
            tenant_id: Tenant identifier for structural isolation (ADR-060).
                When provided, vector search results are scoped to this
                tenant at the adapter level.

        Returns:
            A ``RAGResult`` containing filtered, ranked results.
        """
        effective_k = k if k is not None else self._default_k
        threshold = similarity_threshold if similarity_threshold is not None else self._threshold

        _log.info(
            "rag_query_start",
            text_len=len(text),
            k=effective_k,
            threshold=threshold,
            filters=filters,
            tenant_id=tenant_id,
        )

        # 1. Embed the query
        query_embedding = await self._embeddings.embed_text(text)

        # 2. Search the vector store (tenant-scoped when tenant_id provided)
        candidates = await self._store.search(
            query_embedding=query_embedding,
            k=effective_k,
            filters=filters,
            tenant_id=tenant_id,
        )

        total_candidates = len(candidates)

        # 3. Filter by similarity threshold
        filtered = [r for r in candidates if r.score >= threshold]

        _log.info(
            "rag_query_done",
            total_candidates=total_candidates,
            after_threshold=len(filtered),
            threshold=threshold,
        )

        return RAGResult(
            query=text,
            results=filtered,
            total_candidates=total_candidates,
        )
