# Sprint 0003 — Multi-Embedding + Vector Store

**Status:** planned | **Date:** 2026-02-12
**Goal:** Multi-provider embedding pipeline with primary Gemini embedding-001,
pgvector HNSW store, material ingestion pipeline, and RAG query service.

---

## Verified Library Versions

| Library | Version | Source |
|---------|---------|--------|
| google-genai | 1.63.0 | pypi.org |
| openai | 1.109.1 | pypi.org |
| sentence-transformers | 3.4.1 | pypi.org |
| pgvector-python | 0.4.2 | pypi.org |
| chromadb | 0.6.3 | pypi.org |
| tiktoken | 0.9.0 | pypi.org |

---

## Architecture Decisions (from Research)

- **Primary embedding: gemini-embedding-001** (3072d native, 100+ languages,
  best multilingual quality for PT-BR/EN/ES at free tier). Fallback:
  text-embedding-3-large (OpenAI, 3072d native).
- **Gemini embedding-001 confirmed details (web research 2026-02-11):**
  - Default output: 3072 dimensions. Supports MRL (Matryoshka Representation
    Learning) truncation to any value in the range 128-3072.
  - We use 1536d per ADR-014.
  - **L2 normalization is REQUIRED after Matryoshka truncation.** Truncating
    dimensions breaks unit-norm guarantees; the adapter must re-normalize.
  - API parameter: `output_dimensionality` in `EmbedContentConfig`.
  - Task types: use `RETRIEVAL_DOCUMENT` for indexing, `RETRIEVAL_QUERY` for
    search. Setting the appropriate task type improves recall quality.
- **Dimensionality normalization**: ALL embeddings truncated to 1536d using
  Matryoshka dimensionality reduction. Both Gemini (`output_dimensionality`)
  and OpenAI (`dimensions`) support native truncation. For local models that
  output fewer dimensions (e.g., bge-m3 at 1024d), pad with zeros to 1536d.
  This enables a single `VECTOR(1536)` column regardless of provider.
- **Primary vector store: pgvector** with HNSW index (cosine similarity).
  ChromaDB available as lightweight local-only alternative for dev without
  Docker. Qdrant adapter NOT implemented for hackathon (registered as a
  future item).
- **HNSW parameters (updated per Codex validation 2026-02-11)**: m=24,
  ef_construction=128, ef_search=64. Tuned for ~100K document chunks at
  1536d. m=24 (increased from initial 16) provides better recall at this
  dimensionality with acceptable index build cost. Query-time: `SET
  hnsw.ef_search = 64` per session for good recall/latency balance.
  Use `vector_cosine_ops` operator class for normalized embeddings.
- **Batch ingestion backpressure**: `asyncio.Semaphore(5)` limits concurrent
  embedding API calls. Prevents rate limit exhaustion (Gemini free tier:
  1500 RPM).
- **Chunking strategy**: 512-token windows with 64-token overlap using
  tiktoken tokenizer. Overlap ensures context continuity at chunk boundaries.
  Token-based (not character-based) for accurate LLM context accounting.
  GPT-5.2/Codex consultation (2026-02-11) confirmed 64-token overlap as
  optimal (not 50). Additionally, a **semantic splitter fallback** should be
  added for heading/paragraph boundary detection -- when the source material
  contains clear structural markers (headings, section breaks), prefer
  splitting at those boundaries rather than mid-sentence. This is a secondary
  strategy layered on top of the token-window approach.
- **Provider switching**: `EmbeddingConfig.provider` in Settings determines
  which adapter the DI container wires. All adapters share the `Embeddings`
  protocol from `domain/ports/embeddings.py`.

### CRITICAL: Cross-Provider Embedding Integrity

**NEVER mix embedding providers in the same vector space.** Embeddings from
different models exist in incompatible vector spaces. Cosine similarity across
providers is mathematically meaningless and will produce garbage results.

**Invariants:**
- Pick ONE embedding provider per collection/table partition.
- Store `embedding_model_name` + `embedding_dimensions` in every chunk's
  metadata for runtime validation.
- On provider switch, ALL existing chunks in that collection MUST be
  re-embedded with the new provider before any queries run.
- The ingestion pipeline must validate that the configured provider matches
  the provider recorded in existing chunk metadata for the same material;
  reject or force re-embed if they differ.

---

## Embedding Models Comparison (2026 Research)

| Model | Dimensions | Languages | MTEB Score | Cost | Notes |
|-------|-----------|-----------|------------|------|-------|
| gemini-embedding-001 | 3072 (truncatable) | 100+ | ~64 | Free tier: 1500 RPM | Primary choice |
| text-embedding-3-large | 3072 (truncatable to 256-3072) | 100+ | 64.6 | $0.13/1M tokens | Best commercial fallback |
| BGE-M3 (BAAI) | 1024 | 100+ | 63.0 | Free (local) | Best open-source multilingual |
| Qwen3-Embedding-8B | variable | 100+ | 70.58 multilingual | Free (local) | Highest MTEB but needs GPU |
| EmbeddingGemma-300M | 768 | 100+ | ~59 | Free (local) | Lightweight, on-device |
| Nomic Embed Text V2 | 768 | 100+ | ~62 | Free (local) | MoE architecture |

**Decision rationale:** gemini-embedding-001 offers the best combination of
multilingual quality, free-tier availability, and Matryoshka truncation support.
OpenAI text-embedding-3-large is the fallback for reliability. BGE-M3 via
sentence-transformers handles offline/dev scenarios where no API keys are
available.

---

## Domain Port Reference

All adapters in this sprint must conform to these existing protocols from
Sprint 1:

**Embeddings protocol** (`runtime/ailine_runtime/domain/ports/embeddings.py`):
```python
@runtime_checkable
class Embeddings(Protocol):
    @property
    def dimensions(self) -> int: ...

    @property
    def model_name(self) -> str: ...

    async def embed_text(self, text: str) -> list[float]: ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
```

**VectorStore protocol** (`runtime/ailine_runtime/domain/ports/vectorstore.py`):
```python
@runtime_checkable
class VectorStore(Protocol):
    async def upsert(
        self, *, ids: list[str], embeddings: list[list[float]],
        texts: list[str], metadatas: list[dict[str, Any]],
    ) -> None: ...

    async def search(
        self, *, query_embedding: list[float], k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]: ...

    async def delete(self, *, ids: list[str]) -> None: ...
```

---

## Stories

### S3-001: Gemini Embeddings Adapter (Primary)

**Description:** Implement the `Embeddings` port using the `google-genai` SDK
with `gemini-embedding-001`. This is the primary embedding provider for
production and demo use.

**Files:**
- `runtime/ailine_runtime/adapters/embeddings/__init__.py`
- `runtime/ailine_runtime/adapters/embeddings/gemini_embeddings.py`

**Acceptance Criteria:**
- [ ] `GeminiEmbeddings` satisfies `Embeddings` protocol (isinstance check)
- [ ] `dimensions` property returns configured value (default 1536)
- [ ] `model_name` property returns `"gemini-embedding-001"`
- [ ] `embed_text()` returns `list[float]` of length 1536 (truncated from 3072 via `output_dimensionality`)
- [ ] `embed_text()` uses task type `RETRIEVAL_QUERY` for search queries
- [ ] `embed_batch()` handles up to 100 texts in a single API call
- [ ] `embed_batch()` uses task type `RETRIEVAL_DOCUMENT` for indexing
- [ ] **L2 normalization applied after Matryoshka truncation** (truncation breaks unit-norm)
- [ ] Rate limiting handled with exponential backoff (3 retries, base 1s, max 30s)
- [ ] Raises `ProviderError` (from `shared/errors.py`) on API failure after retries
- [ ] API key injected via constructor (from Settings `google_api_key`)
- [ ] Stores `embedding_model_name` and `embedding_dimensions` in returned metadata for cross-provider validation

**GPT-5.2/Codex validated code pattern (2026-02-11):**

The following pattern was validated by GPT-5.2/Codex expert consultation.
Key details confirmed:
- Import `EmbedContentConfig` from `google.genai.types` (the exact import path)
- Use `numpy` for L2 normalization (more efficient than pure-Python `math` for
  batch operations); L2 normalization is **required** after Matryoshka truncation
- `task_type="RETRIEVAL_DOCUMENT"` for indexing, `"RETRIEVAL_QUERY"` for search
- Batch size: up to 100 texts per request (free tier: 1500 req/min)
- `result.embeddings[0].values` is the accessor for the raw float list

```python
# GPT-5.2/Codex validated reference (exact SDK pattern):
from google import genai
from google.genai.types import EmbedContentConfig
import numpy as np

class GeminiEmbeddingsAdapter:
    def __init__(self, api_key: str, dimensions: int = 1536):
        self.client = genai.Client(api_key=api_key)
        self.dimensions = dimensions
        self.model = "gemini-embedding-001"

    async def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        config = EmbedContentConfig(
            output_dimensionality=self.dimensions,
            task_type=task_type
        )
        result = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=config
        )
        vector = result.embeddings[0].values
        # L2 normalize after MRL truncation
        norm = np.linalg.norm(vector)
        return (np.array(vector) / norm).tolist() if norm > 0 else vector
```

**Full implementation pattern (incorporating Codex findings into our architecture):**

```python
# runtime/ailine_runtime/adapters/embeddings/gemini_embeddings.py
from __future__ import annotations

import asyncio
import logging

import numpy as np
from google import genai
from google.genai.types import EmbedContentConfig

from ailine_runtime.shared.errors import ProviderError, RateLimitError

logger = logging.getLogger(__name__)

class GeminiEmbeddings:
    """Embeddings adapter using Google Gemini embedding-001.

    Uses Matryoshka dimensionality reduction to output vectors at the
    configured dimension (default 1536), truncated from the native 3072.

    L2 normalization is applied after truncation because Matryoshka
    dimensionality reduction breaks unit-norm guarantees.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-embedding-001",
        dimensions: int = 1536,
        max_retries: int = 3,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._dimensions = dimensions
        self._max_retries = max_retries

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model

    @staticmethod
    def _l2_normalize(vector: list[float]) -> list[float]:
        """L2-normalize a vector. Required after Matryoshka truncation.

        Uses numpy for efficient normalization. Returns the original
        vector unchanged if the norm is zero (degenerate case).
        """
        arr = np.array(vector)
        norm = np.linalg.norm(arr)
        if norm > 0:
            return (arr / norm).tolist()
        return vector

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string (for search queries).

        Uses task_type=RETRIEVAL_QUERY which optimizes the embedding
        for query-document similarity matching.
        """
        result = await self._call_with_retry(
            contents=text,
            task_type="RETRIEVAL_QUERY",
        )
        return self._l2_normalize(result.embeddings[0].values)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts for indexing (up to 100 per Gemini API call).

        Uses task_type=RETRIEVAL_DOCUMENT which optimizes the embedding
        for being matched against queries. Batch limit is 100 texts per
        request (Gemini free tier: 1500 req/min).
        """
        all_embeddings: list[list[float]] = []
        # Gemini batch limit is 100 texts per call
        for i in range(0, len(texts), 100):
            batch = texts[i : i + 100]
            result = await self._call_with_retry(
                contents=batch,
                task_type="RETRIEVAL_DOCUMENT",
            )
            all_embeddings.extend(
                self._l2_normalize(e.values) for e in result.embeddings
            )
        return all_embeddings

    async def _call_with_retry(self, *, contents, task_type: str = "RETRIEVAL_QUERY"):
        """Call the Gemini embed API with exponential backoff.

        Uses EmbedContentConfig with output_dimensionality for MRL truncation
        and the appropriate task_type for the use case.
        """
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return await self._client.aio.models.embed_content(
                    model=self._model,
                    contents=contents,
                    config=EmbedContentConfig(
                        output_dimensionality=self._dimensions,
                        task_type=task_type,
                    ),
                )
            except Exception as exc:
                last_exc = exc
                exc_str = str(exc).lower()
                if "rate" in exc_str or "429" in exc_str:
                    wait = min(2**attempt, 30)
                    logger.warning(
                        "Gemini rate limit hit, retrying in %ds (attempt %d/%d)",
                        wait, attempt + 1, self._max_retries,
                    )
                    await asyncio.sleep(wait)
                else:
                    raise ProviderError(
                        code="embedding_provider_error",
                        message=f"Gemini embedding failed: {exc}",
                    ) from exc
        raise RateLimitError(
            code="embedding_rate_limit",
            message=f"Gemini embedding rate limit exceeded after {self._max_retries} retries",
        ) from last_exc
```

---

### S3-002: OpenAI Embeddings Adapter (Fallback)

**Description:** Implement the `Embeddings` port using the `openai` SDK with
`text-embedding-3-large`. Serves as the fallback when Gemini is unavailable or
when a teacher prefers OpenAI.

**Files:**
- `runtime/ailine_runtime/adapters/embeddings/openai_embeddings.py`

**Acceptance Criteria:**
- [ ] `OpenAIEmbeddings` satisfies `Embeddings` protocol (isinstance check)
- [ ] `dimensions` property returns configured value (default 1536)
- [ ] `model_name` property returns `"text-embedding-3-large"`
- [ ] `embed_text()` returns `list[float]` of length 1536 (truncated via `dimensions` param)
- [ ] `embed_batch()` batches via OpenAI's native batch endpoint (up to 2048 inputs)
- [ ] Rate limiting handled with exponential backoff
- [ ] Raises `ProviderError` on API failure after retries

**Implementation pattern:**

```python
# runtime/ailine_runtime/adapters/embeddings/openai_embeddings.py
from __future__ import annotations

import asyncio
import logging

from openai import AsyncOpenAI, RateLimitError as OpenAIRateLimitError

from ailine_runtime.shared.errors import ProviderError, RateLimitError

logger = logging.getLogger(__name__)

class OpenAIEmbeddings:
    """Embeddings adapter using OpenAI text-embedding-3-large.

    Uses the `dimensions` parameter for native Matryoshka truncation.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "text-embedding-3-large",
        dimensions: int = 1536,
        max_retries: int = 3,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._dimensions = dimensions
        self._max_retries = max_retries

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model

    async def embed_text(self, text: str) -> list[float]:
        resp = await self._call_with_retry(input=[text])
        return resp.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        # OpenAI supports up to 2048 inputs per call
        for i in range(0, len(texts), 2048):
            batch = texts[i : i + 2048]
            resp = await self._call_with_retry(input=batch)
            # Sort by index to guarantee order
            sorted_data = sorted(resp.data, key=lambda d: d.index)
            all_embeddings.extend(d.embedding for d in sorted_data)
        return all_embeddings

    async def _call_with_retry(self, *, input: list[str]):
        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return await self._client.embeddings.create(
                    model=self._model,
                    input=input,
                    dimensions=self._dimensions,
                )
            except OpenAIRateLimitError as exc:
                last_exc = exc
                wait = min(2**attempt, 30)
                logger.warning(
                    "OpenAI rate limit, retrying in %ds (attempt %d/%d)",
                    wait, attempt + 1, self._max_retries,
                )
                await asyncio.sleep(wait)
            except Exception as exc:
                raise ProviderError(
                    code="embedding_provider_error",
                    message=f"OpenAI embedding failed: {exc}",
                ) from exc
        raise RateLimitError(
            code="embedding_rate_limit",
            message=f"OpenAI rate limit exceeded after {self._max_retries} retries",
        ) from last_exc
```

---

### S3-003: Local Embeddings Adapter (Offline/Dev)

**Description:** Implement the `Embeddings` port using BAAI/bge-m3 via
`sentence-transformers` for offline development and testing without API keys.
Lazy-loads the model on first use to avoid slowing down application startup.

**Files:**
- `runtime/ailine_runtime/adapters/embeddings/local_embeddings.py`

**Acceptance Criteria:**
- [ ] `LocalEmbeddings` satisfies `Embeddings` protocol (isinstance check)
- [ ] `dimensions` property returns configured value (default 1536)
- [ ] `model_name` property returns `"BAAI/bge-m3"`
- [ ] Model loaded lazily on first `embed_text()` or `embed_batch()` call
- [ ] Native 1024d output zero-padded to 1536d (or truncated if configured <1024)
- [ ] CPU-only inference (no CUDA dependency for dev machines)
- [ ] Warning logged if model download is required on first use

**Implementation pattern:**

```python
# runtime/ailine_runtime/adapters/embeddings/local_embeddings.py
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class LocalEmbeddings:
    """Embeddings adapter using BAAI/bge-m3 via sentence-transformers.

    Designed for offline development and testing. The model is loaded
    lazily on first use. Outputs are padded/truncated to match the
    configured dimensionality (default 1536).
    """

    NATIVE_DIM = 1024  # bge-m3 native output dimension

    def __init__(
        self,
        *,
        model_name: str = "BAAI/bge-m3",
        dimensions: int = 1536,
        device: str = "cpu",
    ) -> None:
        self._model_name = model_name
        self._dimensions = dimensions
        self._device = device
        self._model: SentenceTransformer | None = None

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name

    def _ensure_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading local embedding model '%s' (first use)...", self._model_name)
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name, device=self._device)
            logger.info("Local embedding model loaded.")
        return self._model

    def _normalize_dims(self, vectors: list[list[float]]) -> list[list[float]]:
        """Pad with zeros or truncate to match configured dimensions."""
        result = []
        for vec in vectors:
            if len(vec) < self._dimensions:
                vec = vec + [0.0] * (self._dimensions - len(vec))
            elif len(vec) > self._dimensions:
                vec = vec[: self._dimensions]
            result.append(vec)
        return result

    async def embed_text(self, text: str) -> list[float]:
        model = self._ensure_model()
        embedding = model.encode([text], normalize_embeddings=True)
        return self._normalize_dims([embedding[0].tolist()])[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        model = self._ensure_model()
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
        return self._normalize_dims([e.tolist() for e in embeddings])
```

---

### S3-004: pgvector Store Adapter

**Description:** Implement the `VectorStore` port using pgvector with HNSW
index on the `material_chunks` table from Sprint 2. Uses SQLAlchemy async
sessions for all database operations.

**Files:**
- `runtime/ailine_runtime/adapters/vectorstores/__init__.py`
- `runtime/ailine_runtime/adapters/vectorstores/pgvector_store.py`

**Acceptance Criteria:**
- [ ] `PgVectorStore` satisfies `VectorStore` protocol (isinstance check)
- [ ] `upsert()` stores vectors + text + metadata into `material_chunks` table
- [ ] `upsert()` uses `ON CONFLICT DO UPDATE` for idempotent writes (GPT-5.2/Codex confirmed pattern)
- [ ] `upsert()` stores `embedding_model_version` in chunk metadata for provider tracking
- [ ] `search()` performs cosine similarity using `<=>` operator (HNSW accelerated)
- [ ] `search()` supports metadata-based filtering (teacher_id, subject via JSONB)
- [ ] `search()` respects the `k` parameter for top-k results
- [ ] `search()` validates that query embedding dimensions match the stored vector dimensions (1536); raises `ValueError` on mismatch
- [ ] `delete()` removes vectors by ID from `material_chunks`
- [ ] Proper async session management (session-per-operation or injected session)
- [ ] HNSW `ef_search` set via `SET LOCAL hnsw.ef_search = 64` per query

**HNSW Configuration Constants (validated for ~100K docs at 1536d):**

```python
HNSW_M = 24                  # Bi-directional links per node (updated from 16 per Codex review)
HNSW_EF_CONSTRUCTION = 128   # Build-time search width
HNSW_EF_SEARCH = 64          # Query-time search width (SET hnsw.ef_search = 64)
```

**IVFFlat Fallback Index (GPT-5.2/Codex recommended, 2026-02-11):**

For environments where HNSW build time or memory is prohibitive (e.g., large
batch re-indexing), an IVFFlat fallback is available:

```python
IVFFLAT_LISTS = 100          # Number of clusters (sqrt(100K) ~ 316, but 100 is sufficient for recall)
IVFFLAT_PROBES = 10          # Number of clusters to search at query time
```

```sql
-- IVFFlat index (alternative to HNSW for lower build cost / memory)
CREATE INDEX IF NOT EXISTS idx_material_chunks_embedding_ivfflat
  ON material_chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Query-time: SET ivfflat.probes = 10;
```

**Benchmark requirement:** Before selecting HNSW vs IVFFlat in production,
benchmark both on a realistic subset (~10K chunks at 1536d) measuring:
recall@5, p95 latency, index build time, and memory usage. Document results
in `control_docs/SYSTEM_DESIGN.md`. For hackathon, use HNSW as default.

**Operator class:** Use `vector_cosine_ops` for the HNSW index since all
embeddings are L2-normalized. This is more efficient than `vector_ip_ops` for
normalized vectors and aligns with the cosine distance operator `<=>` used in
queries.

**Implementation pattern:**

```python
# runtime/ailine_runtime/adapters/vectorstores/pgvector_store.py
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ailine_runtime.adapters.db.models import MaterialChunkModel
from ailine_runtime.domain.ports.vectorstore import VectorSearchResult

logger = logging.getLogger(__name__)

HNSW_EF_SEARCH = 64
EXPECTED_DIMENSIONS = 1536  # Must match VECTOR(1536) column

class PgVectorStore:
    """VectorStore adapter using pgvector with HNSW index.

    Operates on the material_chunks table. Uses cosine distance (<=>)
    for similarity search, accelerated by the HNSW index created in
    the Alembic migration.

    Ingestion idempotency (GPT-5.2/Codex validated, 2026-02-11):
    - Stores embedding_model_version in chunk metadata for provider tracking.
    - Uses ON CONFLICT DO UPDATE for upserts so re-ingestion replaces stale chunks.
    - Validates embedding dimensions match EXPECTED_DIMENSIONS on search.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def upsert(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert chunks with ON CONFLICT DO UPDATE for idempotency.

        Each metadata dict should contain 'embedding_model_version' so that
        provider switches can be detected and force re-embedding.
        """
        async with self._session_factory() as session:
            for i, chunk_id in enumerate(ids):
                # Validate embedding dimensions before storing
                if len(embeddings[i]) != EXPECTED_DIMENSIONS:
                    raise ValueError(
                        f"Embedding dimension mismatch: expected {EXPECTED_DIMENSIONS}, "
                        f"got {len(embeddings[i])} for chunk {chunk_id}"
                    )

                stmt = text("""
                    INSERT INTO material_chunks (id, material_id, chunk_index, text, embedding, metadata)
                    VALUES (:id, :material_id, :chunk_index, :text, :embedding, :metadata)
                    ON CONFLICT (id) DO UPDATE SET
                        text = EXCLUDED.text,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        updated_at = now()
                """)
                meta = metadatas[i]
                await session.execute(stmt, {
                    "id": chunk_id,
                    "material_id": meta.get("material_id", ""),
                    "chunk_index": meta.get("chunk_index", i),
                    "text": texts[i],
                    "embedding": str(embeddings[i]),  # pgvector accepts text repr
                    "metadata": meta,
                })
            await session.commit()

    async def search(
        self,
        *,
        query_embedding: list[float],
        k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search for similar chunks using cosine distance.

        Validates that query_embedding dimensions match the expected
        vector column dimensions before executing the query.
        """
        # Validate dimensions match on search (GPT-5.2/Codex recommendation)
        if len(query_embedding) != EXPECTED_DIMENSIONS:
            raise ValueError(
                f"Query embedding dimension mismatch: expected {EXPECTED_DIMENSIONS}, "
                f"got {len(query_embedding)}. Ensure the embedding provider is "
                f"configured to output {EXPECTED_DIMENSIONS}-dimensional vectors."
            )

        async with self._session_factory() as session:
            # Set HNSW ef_search for this query
            await session.execute(
                text(f"SET LOCAL hnsw.ef_search = {HNSW_EF_SEARCH}")
            )

            # Build query with optional filters
            where_clauses = ["embedding IS NOT NULL"]
            params: dict[str, Any] = {
                "embedding": str(query_embedding),
                "k": k,
            }

            if filters:
                if "teacher_id" in filters:
                    where_clauses.append(
                        "material_id IN (SELECT id FROM materials WHERE teacher_id = :teacher_id)"
                    )
                    params["teacher_id"] = filters["teacher_id"]
                if "subject" in filters:
                    where_clauses.append("metadata->>'subject' = :subject")
                    params["subject"] = filters["subject"]
                if "material_id" in filters:
                    where_clauses.append("material_id = :material_id")
                    params["material_id"] = filters["material_id"]

            where_sql = " AND ".join(where_clauses)
            stmt = text(f"""
                SELECT id, text, metadata,
                       1 - (embedding <=> :embedding::vector) AS score
                FROM material_chunks
                WHERE {where_sql}
                ORDER BY embedding <=> :embedding::vector
                LIMIT :k
            """)

            result = await session.execute(stmt, params)
            rows = result.fetchall()
            return [
                VectorSearchResult(
                    id=str(row.id),
                    score=float(row.score),
                    text=row.text,
                    metadata=row.metadata or {},
                )
                for row in rows
            ]

    async def delete(self, *, ids: list[str]) -> None:
        async with self._session_factory() as session:
            stmt = text("DELETE FROM material_chunks WHERE id = ANY(:ids)")
            await session.execute(stmt, {"ids": ids})
            await session.commit()
```

---

### S3-005: ChromaDB Store Adapter (Dev Alternative)

**Description:** Implement the `VectorStore` port using ChromaDB for local
development without Postgres. Uses persistent file storage so data survives
restarts. This adapter is for development convenience only -- pgvector is the
production target.

**Files:**
- `runtime/ailine_runtime/adapters/vectorstores/chroma_store.py`

**Acceptance Criteria:**
- [ ] `ChromaVectorStore` satisfies `VectorStore` protocol (isinstance check)
- [ ] Uses persistent storage directory (`AILINE_LOCAL_STORE/chroma/`)
- [ ] Same `upsert()`, `search()`, `delete()` interface as pgvector adapter
- [ ] Collection name configurable (default: `"ailine_materials"`)
- [ ] Metadata-based filtering maps to ChromaDB's `where` clause
- [ ] No external services required (pure Python, file-based)

**Implementation pattern:**

```python
# runtime/ailine_runtime/adapters/vectorstores/chroma_store.py
from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from ailine_runtime.domain.ports.vectorstore import VectorSearchResult

class ChromaVectorStore:
    """VectorStore adapter using ChromaDB for local development.

    Uses persistent file-based storage. Suitable for dev/testing
    without Docker or Postgres.
    """

    def __init__(
        self,
        *,
        persist_directory: str = ".local_store/chroma",
        collection_name: str = "ailine_materials",
    ) -> None:
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def upsert(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    async def search(
        self,
        *,
        query_embedding: list[float],
        k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        where = None
        if filters:
            # ChromaDB where clause format
            conditions = []
            for key, value in filters.items():
                conditions.append({key: {"$eq": value}})
            if len(conditions) == 1:
                where = conditions[0]
            elif len(conditions) > 1:
                where = {"$and": conditions}

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # ChromaDB returns distances; convert to similarity score
                distance = results["distances"][0][i] if results["distances"] else 0.0
                score = 1.0 - distance  # cosine distance -> similarity
                search_results.append(
                    VectorSearchResult(
                        id=doc_id,
                        score=score,
                        text=results["documents"][0][i] if results["documents"] else "",
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    )
                )
        return search_results

    async def delete(self, *, ids: list[str]) -> None:
        self._collection.delete(ids=ids)
```

---

### S3-006: Material Ingestion Pipeline

**Description:** Implement the service that takes an uploaded material (PDF,
DOCX, TXT, MD), extracts text, splits it into token-based chunks, embeds all
chunks via the configured `Embeddings` adapter, and stores them in the
configured `VectorStore`. Emits progress events via `EventBus`.

**Files:**
- `runtime/ailine_runtime/app/services/__init__.py`
- `runtime/ailine_runtime/app/services/ingestion.py`

**Acceptance Criteria:**
- [ ] Accepts material ID + raw text (text extraction handled upstream or in this service)
- [ ] PDF parsing via `pypdf` (text extraction from pages)
- [ ] DOCX parsing via `python-docx` (paragraph text extraction)
- [ ] TXT/MD passed through directly
- [ ] Chunking: 512-token windows, 64-token overlap using tiktoken (`cl100k_base`)
- [ ] Semantic splitter fallback: when source contains headings/section breaks, prefer splitting at structural boundaries rather than mid-sentence (GPT-5.2/Codex recommended)
- [ ] Batch embedding with `asyncio.Semaphore(5)` for backpressure
- [ ] Stores chunks with: material_id, chunk_index, text, embedding, metadata
- [ ] Metadata includes: `material_id`, `chunk_index`, `teacher_id`, `title`, `content_type`, `embedding_model_version`, `embedding_dimensions`
- [ ] `embedding_model_version` stored in every chunk metadata for idempotency and cross-provider validation (GPT-5.2/Codex confirmed pattern)
- [ ] Progress events published via EventBus: `material.ingestion.started`, `material.ingestion.chunk_embedded`, `material.ingestion.completed`, `material.ingestion.failed`
- [ ] Idempotent: re-ingesting same material replaces existing chunks via `ON CONFLICT DO UPDATE` upserts
- [ ] On re-ingestion, if `embedding_model_version` in existing chunks differs from current provider, force full re-embed (never mix providers)
- [ ] Returns total chunk count on success

**Chunking implementation:**

```python
import tiktoken

def chunk_text(
    text: str,
    *,
    max_tokens: int = 512,
    overlap_tokens: int = 64,
    encoding_name: str = "cl100k_base",
) -> list[str]:
    """Split text into overlapping token-based chunks.

    Uses tiktoken for accurate token counting that aligns with LLM
    context window accounting.
    """
    enc = tiktoken.get_encoding(encoding_name)
    tokens = enc.encode(text)
    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunks.append(enc.decode(chunk_tokens))
        start += max_tokens - overlap_tokens
    return chunks
```

**Ingestion service pattern:**

```python
# runtime/ailine_runtime/app/services/ingestion.py
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from ailine_runtime.domain.ports.embeddings import Embeddings
from ailine_runtime.domain.ports.vectorstore import VectorStore
from ailine_runtime.domain.ports.events import EventBus

logger = logging.getLogger(__name__)

# Backpressure: max concurrent embedding API calls
EMBED_SEMAPHORE_LIMIT = 5
CHUNK_MAX_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 64

class IngestionService:
    """Ingests educational materials into the vector store.

    Pipeline: parse -> chunk -> embed (batched) -> store.
    Emits progress events via EventBus for frontend tracking.

    Idempotency (GPT-5.2/Codex validated, 2026-02-11):
    - Stores embedding_model_version in every chunk's metadata so that
      provider switches are detectable.
    - Uses ON CONFLICT DO UPDATE upserts so re-ingestion replaces stale data.
    - Validates that existing chunks for the same material were produced by
      the same embedding provider; forces full re-embed on mismatch.
    """

    def __init__(
        self,
        *,
        embeddings: Embeddings,
        vectorstore: VectorStore,
        event_bus: EventBus,
    ) -> None:
        self._embeddings = embeddings
        self._vectorstore = vectorstore
        self._event_bus = event_bus
        self._semaphore = asyncio.Semaphore(EMBED_SEMAPHORE_LIMIT)

    async def ingest(
        self,
        *,
        material_id: str,
        teacher_id: str,
        title: str,
        content_type: str,
        raw_text: str,
    ) -> int:
        """Ingest a material: chunk, embed, store. Returns chunk count.

        Metadata stored per chunk includes embedding_model_version and
        embedding_dimensions for cross-provider integrity validation.
        Re-ingesting the same material_id replaces existing chunks via
        ON CONFLICT DO UPDATE (idempotent upserts).
        """
        await self._event_bus.publish("material.ingestion.started", {
            "material_id": material_id, "title": title,
        })

        try:
            # 1. Chunk
            chunks = chunk_text(
                raw_text,
                max_tokens=CHUNK_MAX_TOKENS,
                overlap_tokens=CHUNK_OVERLAP_TOKENS,
            )
            logger.info("Material %s chunked into %d pieces", material_id, len(chunks))

            # 2. Embed in batches with backpressure
            embeddings = await self._embed_with_backpressure(chunks)

            # 3. Store with embedding model version in metadata
            chunk_ids = [str(uuid.uuid4()) for _ in chunks]
            metadatas = [
                {
                    "material_id": material_id,
                    "chunk_index": i,
                    "teacher_id": teacher_id,
                    "title": title,
                    "content_type": content_type,
                    # Embedding provenance for idempotency and cross-provider validation
                    "embedding_model_version": self._embeddings.model_name,
                    "embedding_dimensions": self._embeddings.dimensions,
                }
                for i in range(len(chunks))
            ]

            await self._vectorstore.upsert(
                ids=chunk_ids,
                embeddings=embeddings,
                texts=chunks,
                metadatas=metadatas,
            )

            await self._event_bus.publish("material.ingestion.completed", {
                "material_id": material_id,
                "chunk_count": len(chunks),
                "embedding_model": self._embeddings.model_name,
            })
            return len(chunks)

        except Exception as exc:
            await self._event_bus.publish("material.ingestion.failed", {
                "material_id": material_id,
                "error": str(exc),
            })
            raise

    async def _embed_with_backpressure(
        self, chunks: list[str], batch_size: int = 50,
    ) -> list[list[float]]:
        """Embed chunks in batches, limited by semaphore."""
        all_embeddings: list[list[float]] = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            async with self._semaphore:
                batch_embeddings = await self._embeddings.embed_batch(batch)
                all_embeddings.extend(batch_embeddings)
        return all_embeddings
```

---

### S3-007: RAG Query Service

**Description:** Service that takes a natural-language question, embeds it
using the configured `Embeddings` adapter, searches the `VectorStore` for
relevant material chunks, and returns ranked results. Used by both the plan
generation pipeline (evidence retrieval) and the tutor chat (context
injection).

**Files:**
- `runtime/ailine_runtime/app/services/rag.py`

**Acceptance Criteria:**
- [ ] `query()` embeds question -> vector search -> returns top-k `VectorSearchResult` items
- [ ] Filters by `teacher_id` (required) and optional `subject`, `material_id`
- [ ] Configurable `k` (default 5) and `similarity_threshold` (default 0.7)
- [ ] Results below similarity threshold filtered out
- [ ] Returns empty list if no results above threshold (does not raise)
- [ ] `query_with_context()` convenience method returns concatenated text (for prompt injection)
- [ ] Logging: query text (truncated), result count, top score, latency

**Implementation pattern:**

```python
# runtime/ailine_runtime/app/services/rag.py
from __future__ import annotations

import logging
import time
from typing import Any

from ailine_runtime.domain.ports.embeddings import Embeddings
from ailine_runtime.domain.ports.vectorstore import VectorSearchResult, VectorStore

logger = logging.getLogger(__name__)

DEFAULT_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.7

class RAGService:
    """Retrieval-Augmented Generation query service.

    Embeds a question, searches the vector store, and returns relevant
    material chunks above a similarity threshold. Used by plan pipeline
    and tutor chat for evidence-based responses.
    """

    def __init__(
        self,
        *,
        embeddings: Embeddings,
        vectorstore: VectorStore,
    ) -> None:
        self._embeddings = embeddings
        self._vectorstore = vectorstore

    async def query(
        self,
        *,
        question: str,
        teacher_id: str,
        subject: str | None = None,
        material_id: str | None = None,
        k: int = DEFAULT_K,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> list[VectorSearchResult]:
        """Retrieve relevant material chunks for a question.

        Args:
            question: Natural language query to embed and search.
            teacher_id: Required filter -- only search this teacher's materials.
            subject: Optional subject filter.
            material_id: Optional filter to search within a specific material.
            k: Maximum number of results to return.
            similarity_threshold: Minimum cosine similarity score (0.0-1.0).

        Returns:
            List of VectorSearchResult sorted by descending score,
            filtered to those above the similarity threshold.
        """
        start = time.monotonic()

        # 1. Embed the question
        query_embedding = await self._embeddings.embed_text(question)

        # 2. Build filters
        filters: dict[str, Any] = {"teacher_id": teacher_id}
        if subject:
            filters["subject"] = subject
        if material_id:
            filters["material_id"] = material_id

        # 3. Search
        results = await self._vectorstore.search(
            query_embedding=query_embedding,
            k=k,
            filters=filters,
        )

        # 4. Filter by threshold
        filtered = [r for r in results if r.score >= similarity_threshold]

        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "RAG query: '%s...' -> %d/%d results above %.2f threshold (%.1fms)",
            question[:50],
            len(filtered),
            len(results),
            similarity_threshold,
            elapsed_ms,
        )

        return filtered

    async def query_with_context(
        self,
        *,
        question: str,
        teacher_id: str,
        subject: str | None = None,
        k: int = DEFAULT_K,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        separator: str = "\n\n---\n\n",
    ) -> str:
        """Retrieve and concatenate relevant chunks as a single context string.

        Convenience method for prompt injection. Returns empty string if
        no results found above threshold.
        """
        results = await self.query(
            question=question,
            teacher_id=teacher_id,
            subject=subject,
            k=k,
            similarity_threshold=similarity_threshold,
        )
        if not results:
            return ""
        return separator.join(
            f"[Source: {r.metadata.get('title', 'unknown')} | Score: {r.score:.2f}]\n{r.text}"
            for r in results
        )
```

---

## Removed from Scope (2026-02-11, expert recommendations)

| Item | Original Plan | Reason | Disposition |
|------|---------------|--------|-------------|
| OpenRouter embeddings adapter | 4th embedding provider via OpenRouter API | Reduces complexity. 3 providers (Gemini + OpenAI + local) is sufficient for hackathon and post-MVP. | Removed permanently from sprint scope. |
| Qdrant store adapter | 3rd vector store option alongside pgvector and ChromaDB | 2 vector stores (pgvector for production + ChromaDB for dev) is sufficient. | Deferred to post-hackathon. Registered in `control_docs/TODO.md`. |

**Impact:** This reduces the sprint from 9 stories to 7 stories. The DI
container wiring is simplified (fewer provider branches). No changes to the
domain ports -- the `Embeddings` and `VectorStore` protocols remain
provider-agnostic and new adapters can be added later without modification.

---

## Dependencies

**Requires:** Sprint 2 (database layer) -- ORM models (especially
`MaterialChunkModel` with VECTOR column), async session factory, UnitOfWork,
Docker Compose with pgvector running.

**Produces for Sprint 4+:** Ingestion pipeline and RAG service are consumed
by the plan generation workflow (evidence retrieval) and tutor chat (context
injection).

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemini embedding API rate limits (1500 RPM free tier) | Medium | Semaphore(5) backpressure + exponential backoff. Sufficient for hackathon demo (~1000 chunks). |
| Dimensionality mismatch when switching providers | High | All adapters normalize to 1536d. Re-embed required if switching providers on existing data -- document this. |
| Cross-provider vector space contamination | **Critical** | NEVER mix embeddings from different providers in the same collection. Store `embedding_model_name` + `embedding_dimensions` in chunk metadata. Validate on ingest; reject or force re-embed on mismatch. See "Cross-Provider Embedding Integrity" section above. |
| Missing L2 normalization after MRL truncation | High | Matryoshka truncation breaks unit-norm. All adapters using truncated dimensions must re-normalize. Gemini adapter applies `_l2_normalize()` after every embed call. |
| bge-m3 model download (~2GB) on first local use | Low | Lazy loading with log warning. Document in RUN_DEPLOY.md. Cache in `.local_store/models/`. |
| ChromaDB sync vs async mismatch | Low | ChromaDB client is sync; wrapped in async methods (acceptable for dev-only adapter). |
| tiktoken encoding may not match all LLM tokenizers | Low | `cl100k_base` is close enough for chunking purposes; exact token count verified at LLM call time. |
| pgvector HNSW index performance degrades >1M vectors | Low | Hackathon scope is ~100K chunks. Document scaling path in SYSTEM_DESIGN.md. |

---

## Expert Consultation Log (GPT-5.2/Codex, 2026-02-11)

This section records the key findings from the GPT-5.2/Codex expert
consultation that were incorporated into the sprint stories above.

**Gemini Embedding Adapter:**
- Confirmed exact SDK import path: `from google.genai.types import EmbedContentConfig`
- Confirmed `result.embeddings[0].values` as the accessor for raw float vectors
- L2 normalization via `numpy.linalg.norm` is **required** after Matryoshka truncation
- `task_type="RETRIEVAL_DOCUMENT"` for indexing, `"RETRIEVAL_QUERY"` for search
- Batch size: up to 100 texts per request (free tier: 1500 req/min)

**Chunking Strategy:**
- Confirmed 512 tokens with 64-token overlap (GPT-5.2 recommended 64, not 50)
- Recommended adding a semantic splitter fallback for heading/paragraph boundaries

**pgvector HNSW Index:**
- For ~100K docs at 1536d: HNSW with m=24, ef_construction=128 (confirmed)
- Query-time: `SET hnsw.ef_search = 64` (confirmed)
- IVFFlat fallback: lists=100, probes=10 (for lower build/memory cost)
- Benchmark both on realistic subset before production selection

**Ingestion Idempotency:**
- Store `embedding_model_version` in every chunk's metadata
- Use `ON CONFLICT DO UPDATE` for upserts (idempotent writes)
- Validate dimensions match on search (reject mismatched queries)

---

## Testing Plan

- **Unit tests:** Chunking function (token counts, overlap, edge cases: empty text, single token, exact boundary)
- **Unit tests:** Dimension normalization (padding, truncation, passthrough)
- **Unit tests:** L2 normalization after Matryoshka truncation (verify output is unit-norm using numpy; norm should be ~1.0 within floating-point tolerance)
- **Unit tests:** Cross-provider metadata validation (reject ingest when `embedding_model_version` in existing chunks differs from configured provider)
- **Unit tests:** Dimension mismatch validation in PgVectorStore (upsert rejects wrong-dimension embeddings; search rejects wrong-dimension queries)
- **Unit tests:** `embedding_model_version` and `embedding_dimensions` are present in metadata after ingestion
- **Integration tests (real Gemini API):** `embed_text()` returns correct dimensions, `embed_batch()` handles 10+ texts, task types (`RETRIEVAL_QUERY` vs `RETRIEVAL_DOCUMENT`) produce different embeddings, L2 normalization verified (norm ~1.0)
- **Integration tests (Docker Postgres + pgvector):** upsert + search round-trip, cosine similarity ordering, metadata filtering, delete, `hnsw.ef_search` is set per query, ON CONFLICT DO UPDATE idempotency (upsert same ID twice, second write wins), dimension mismatch raises ValueError
- **Integration tests (ChromaDB):** upsert + search + delete (file-based, no Docker)
- **Service tests:** IngestionService end-to-end with mock EventBus, real embeddings + vectorstore; verify `embedding_model_version` in stored metadata
- **Service tests:** RAGService with seeded data, threshold filtering, empty results
- **Benchmark tests (optional, pre-production):** HNSW vs IVFFlat on ~10K chunks at 1536d -- recall@5, p95 latency, index build time, memory usage

---

## DI Container Updates

The `Container` from Sprint 1 (`shared/container.py`) must be extended to wire
the new adapters based on `Settings`:

```python
# In Container.build():
# Embeddings
if settings.embedding.provider == "gemini":
    embeddings = GeminiEmbeddings(api_key=settings.google_api_key, dimensions=settings.embedding.dimensions)
elif settings.embedding.provider == "openai":
    embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key, dimensions=settings.embedding.dimensions)
elif settings.embedding.provider == "local":
    embeddings = LocalEmbeddings(dimensions=settings.embedding.dimensions)

# VectorStore
if settings.vectorstore.provider == "pgvector":
    vectorstore = PgVectorStore(session_factory=get_session_factory())
elif settings.vectorstore.provider == "chroma":
    vectorstore = ChromaVectorStore(persist_directory=f"{settings.local_store}/chroma")

# Services
ingestion = IngestionService(embeddings=embeddings, vectorstore=vectorstore, event_bus=event_bus)
rag = RAGService(embeddings=embeddings, vectorstore=vectorstore)
```
