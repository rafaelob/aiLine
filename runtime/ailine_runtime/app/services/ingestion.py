"""Material ingestion pipeline.

Takes raw text content, splits it into overlapping chunks, embeds each
chunk, and upserts them into the configured vector store.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from ...domain.ports.embeddings import Embeddings
from ...domain.ports.vectorstore import VectorStore
from ...shared.observability import get_logger

_log = get_logger("ailine.app.services.ingestion")

# Default chunking parameters per ADR conventions
DEFAULT_CHUNK_SIZE = 512  # tokens (approx words for simple tokenizer)
DEFAULT_CHUNK_OVERLAP = 64


@dataclass(frozen=True)
class ChunkingConfig:
    """Configuration for the text chunking stage.

    Args:
        chunk_size: Maximum number of tokens per chunk.
        chunk_overlap: Number of overlapping tokens between consecutive
            chunks for context continuity.
    """

    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP


@dataclass(frozen=True)
class IngestionResult:
    """Summary of a completed ingestion run.

    Attributes:
        material_id: The unique material identifier.
        chunk_count: Number of chunks produced and stored.
        chunk_ids: List of generated chunk IDs.
    """

    material_id: str
    chunk_count: int
    chunk_ids: list[str] = field(default_factory=list)


class IngestionService:
    """Orchestrates the material ingestion pipeline.

    Pipeline stages:
    1. **Chunk** -- split raw text into overlapping windows of tokens.
    2. **Embed** -- batch-embed all chunks via the configured provider.
    3. **Store** -- upsert chunk embeddings + metadata into the vector store.

    Args:
        embeddings: An adapter satisfying the ``Embeddings`` protocol.
        vector_store: An adapter satisfying the ``VectorStore`` protocol.
        chunking: Optional chunking configuration overrides.
    """

    def __init__(
        self,
        *,
        embeddings: Embeddings,
        vector_store: VectorStore,
        chunking: ChunkingConfig | None = None,
    ) -> None:
        self._embeddings = embeddings
        self._store = vector_store
        self._chunking = chunking or ChunkingConfig()

    async def ingest(
        self,
        *,
        text: str,
        material_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> IngestionResult:
        """Ingest raw text into the vector store.

        Args:
            text: The full text content to ingest.
            material_id: Optional identifier for the source material.
                Generated if not provided.
            metadata: Optional base metadata to attach to every chunk.
                Keys like ``teacher_id`` and ``subject`` are typical.
            tenant_id: Tenant identifier for structural isolation (ADR-060).
                Stored alongside each chunk so that searches can be
                scoped to the owning tenant.

        Returns:
            An ``IngestionResult`` summarizing the operation.
        """
        mat_id = material_id or str(uuid.uuid4())
        base_meta = dict(metadata) if metadata else {}
        base_meta["material_id"] = mat_id

        _log.info(
            "ingestion_start",
            material_id=mat_id,
            text_len=len(text),
            chunk_size=self._chunking.chunk_size,
            chunk_overlap=self._chunking.chunk_overlap,
        )

        # 1. Chunk
        chunks = chunk_text(
            text,
            chunk_size=self._chunking.chunk_size,
            chunk_overlap=self._chunking.chunk_overlap,
        )

        if not chunks:
            _log.warning("ingestion_empty", material_id=mat_id)
            return IngestionResult(material_id=mat_id, chunk_count=0)

        # 2. Embed
        embeddings = await self._embeddings.embed_batch(chunks)

        # 3. Build IDs and metadata per chunk
        chunk_ids: list[str] = []
        chunk_metas: list[dict[str, Any]] = []

        for idx in range(len(chunks)):
            chunk_id = f"{mat_id}__chunk_{idx:04d}"
            chunk_ids.append(chunk_id)

            meta = dict(base_meta)
            meta["chunk_index"] = idx
            meta["chunk_count"] = len(chunks)
            chunk_metas.append(meta)

        # 4. Upsert (tenant-scoped when tenant_id provided -- ADR-060)
        await self._store.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            texts=chunks,
            metadatas=chunk_metas,
            tenant_id=tenant_id,
        )

        _log.info(
            "ingestion_done",
            material_id=mat_id,
            chunk_count=len(chunks),
        )

        return IngestionResult(
            material_id=mat_id,
            chunk_count=len(chunks),
            chunk_ids=chunk_ids,
        )


# -- Chunking utility --------------------------------------------------------


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split *text* into overlapping chunks of approximately *chunk_size* words.

    Uses whitespace tokenization as a simple, dependency-free approach.
    For production, consider replacing with ``tiktoken`` for token-accurate
    splitting aligned with the embedding model's tokenizer.

    Args:
        text: The input text.
        chunk_size: Maximum words per chunk.
        chunk_overlap: Number of overlapping words between consecutive chunks.

    Returns:
        List of text chunks.  Empty list if the input is blank.

    Raises:
        ValueError: If ``chunk_overlap >= chunk_size``.
    """
    if chunk_overlap >= chunk_size:
        raise ValueError(f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})")

    words = text.split()
    if not words:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[str] = []

    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        chunk = " ".join(window)
        if chunk.strip():
            chunks.append(chunk)

        # Stop if this window reached the end
        if start + chunk_size >= len(words):
            break

    return chunks
