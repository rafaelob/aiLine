"""Tests for VectorStore adapters, ingestion pipeline, and RAG service.

Covers:
- InMemoryVectorStore: upsert, search, delete, filters, edge cases.
- IngestionService: chunking, end-to-end pipeline with FakeEmbeddings.
- RAGService: query, filtering, threshold behavior.
"""

from __future__ import annotations

import pytest

from ailine_runtime.adapters.embeddings.fake_embeddings import FakeEmbeddings
from ailine_runtime.adapters.vectorstores.inmemory_store import InMemoryVectorStore
from ailine_runtime.app.services.ingestion import (
    ChunkingConfig,
    IngestionService,
    chunk_text,
)
from ailine_runtime.app.services.rag import RAGService
from ailine_runtime.domain.ports.vectorstore import VectorSearchResult, VectorStore

# =============================================================================
# InMemoryVectorStore tests
# =============================================================================


@pytest.fixture
def store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.fixture
def embeddings() -> FakeEmbeddings:
    return FakeEmbeddings(dimensions=64)


class TestInMemoryProtocol:
    """Verify InMemoryVectorStore satisfies the VectorStore protocol."""

    def test_is_runtime_checkable(self, store: InMemoryVectorStore):
        assert isinstance(store, VectorStore)


class TestUpsert:
    """Upsert operations."""

    async def test_upsert_single(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["doc1"],
            embeddings=[[1.0, 0.0, 0.0]],
            texts=["hello"],
            metadatas=[{"source": "test"}],
        )
        assert store.count == 1

    async def test_upsert_multiple(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a", "b", "c"],
            embeddings=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            texts=["alpha", "beta", "gamma"],
            metadatas=[{}, {}, {}],
        )
        assert store.count == 3

    async def test_upsert_overwrites_existing(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["doc1"],
            embeddings=[[1.0, 0.0]],
            texts=["original"],
            metadatas=[{"v": 1}],
        )
        await store.upsert(
            ids=["doc1"],
            embeddings=[[0.0, 1.0]],
            texts=["updated"],
            metadatas=[{"v": 2}],
        )
        assert store.count == 1
        results = await store.search(query_embedding=[0.0, 1.0], k=1)
        assert results[0].text == "updated"
        assert results[0].metadata["v"] == 2

    async def test_upsert_empty(self, store: InMemoryVectorStore):
        await store.upsert(ids=[], embeddings=[], texts=[], metadatas=[])
        assert store.count == 0


class TestSearch:
    """Search operations."""

    async def test_search_returns_most_similar(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["x", "y"],
            embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            texts=["along x", "along y"],
            metadatas=[{}, {}],
        )
        results = await store.search(query_embedding=[1.0, 0.0, 0.0], k=2)
        assert len(results) == 2
        assert results[0].id == "x"
        assert results[0].score > results[1].score

    async def test_search_result_type(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a"],
            embeddings=[[1.0, 0.0]],
            texts=["test"],
            metadatas=[{"key": "val"}],
        )
        results = await store.search(query_embedding=[1.0, 0.0], k=1)
        r = results[0]
        assert isinstance(r, VectorSearchResult)
        assert r.id == "a"
        assert isinstance(r.score, float)
        assert r.text == "test"
        assert r.metadata == {"key": "val"}

    async def test_search_respects_k(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a", "b", "c"],
            embeddings=[[1, 0], [0.9, 0.1], [0, 1]],
            texts=["a", "b", "c"],
            metadatas=[{}, {}, {}],
        )
        results = await store.search(query_embedding=[1, 0], k=2)
        assert len(results) == 2

    async def test_search_empty_store(self, store: InMemoryVectorStore):
        results = await store.search(query_embedding=[1, 0], k=5)
        assert results == []

    async def test_search_zero_query_vector(self, store: InMemoryVectorStore):
        """A zero vector query should return no results (division by zero guard)."""
        await store.upsert(
            ids=["a"],
            embeddings=[[1.0, 0.0]],
            texts=["data"],
            metadatas=[{}],
        )
        results = await store.search(query_embedding=[0.0, 0.0], k=5)
        assert results == []

    async def test_search_scores_are_cosine_similarity(self, store: InMemoryVectorStore):
        """Identical vectors should have similarity ~1.0."""
        await store.upsert(
            ids=["same"],
            embeddings=[[0.6, 0.8]],
            texts=["same"],
            metadatas=[{}],
        )
        results = await store.search(query_embedding=[0.6, 0.8], k=1)
        assert abs(results[0].score - 1.0) < 1e-5

    async def test_search_skips_zero_norm_chunk(self, store: InMemoryVectorStore):
        """Chunks with zero-norm embeddings are skipped during search (line 98)."""
        await store.upsert(
            ids=["zero", "valid"],
            embeddings=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
            texts=["zero embedding", "valid embedding"],
            metadatas=[{}, {}],
        )
        results = await store.search(query_embedding=[1.0, 0.0, 0.0], k=10)
        # The zero-norm chunk should be excluded
        assert len(results) == 1
        assert results[0].id == "valid"

    async def test_search_orthogonal_vectors(self, store: InMemoryVectorStore):
        """Orthogonal vectors should have similarity ~0.0."""
        await store.upsert(
            ids=["orth"],
            embeddings=[[1.0, 0.0]],
            texts=["orthogonal"],
            metadatas=[{}],
        )
        results = await store.search(query_embedding=[0.0, 1.0], k=1)
        assert abs(results[0].score) < 1e-5


class TestSearchFilters:
    """Metadata filtering during search."""

    async def test_filter_by_single_key(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a", "b"],
            embeddings=[[1, 0], [0.9, 0.1]],
            texts=["alice", "bob"],
            metadatas=[{"teacher_id": "t1"}, {"teacher_id": "t2"}],
        )
        results = await store.search(
            query_embedding=[1, 0], k=10, filters={"teacher_id": "t1"}
        )
        assert len(results) == 1
        assert results[0].id == "a"

    async def test_filter_by_multiple_keys(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a", "b", "c"],
            embeddings=[[1, 0], [0.9, 0.1], [0.8, 0.2]],
            texts=["x", "y", "z"],
            metadatas=[
                {"teacher_id": "t1", "subject": "math"},
                {"teacher_id": "t1", "subject": "science"},
                {"teacher_id": "t2", "subject": "math"},
            ],
        )
        results = await store.search(
            query_embedding=[1, 0],
            k=10,
            filters={"teacher_id": "t1", "subject": "math"},
        )
        assert len(results) == 1
        assert results[0].id == "a"

    async def test_filter_no_matches(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a"],
            embeddings=[[1, 0]],
            texts=["data"],
            metadatas=[{"teacher_id": "t1"}],
        )
        results = await store.search(
            query_embedding=[1, 0], k=10, filters={"teacher_id": "t99"}
        )
        assert results == []

    async def test_none_filters_returns_all(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a", "b"],
            embeddings=[[1, 0], [0, 1]],
            texts=["x", "y"],
            metadatas=[{}, {}],
        )
        results = await store.search(query_embedding=[1, 0], k=10, filters=None)
        assert len(results) == 2


class TestDelete:
    """Delete operations."""

    async def test_delete_single(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a", "b"],
            embeddings=[[1, 0], [0, 1]],
            texts=["x", "y"],
            metadatas=[{}, {}],
        )
        await store.delete(ids=["a"])
        assert store.count == 1
        results = await store.search(query_embedding=[1, 0], k=10)
        assert len(results) == 1
        assert results[0].id == "b"

    async def test_delete_multiple(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a", "b", "c"],
            embeddings=[[1, 0], [0, 1], [1, 1]],
            texts=["x", "y", "z"],
            metadatas=[{}, {}, {}],
        )
        await store.delete(ids=["a", "c"])
        assert store.count == 1

    async def test_delete_nonexistent(self, store: InMemoryVectorStore):
        """Deleting a non-existent ID should not raise."""
        await store.delete(ids=["does_not_exist"])
        assert store.count == 0

    async def test_delete_empty_list(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a"],
            embeddings=[[1]],
            texts=["x"],
            metadatas=[{}],
        )
        await store.delete(ids=[])
        assert store.count == 1


class TestStoreClear:
    """Test the clear helper."""

    async def test_clear(self, store: InMemoryVectorStore):
        await store.upsert(
            ids=["a", "b"],
            embeddings=[[1, 0], [0, 1]],
            texts=["x", "y"],
            metadatas=[{}, {}],
        )
        store.clear()
        assert store.count == 0


# =============================================================================
# Chunking function tests
# =============================================================================


class TestChunkText:
    """Test the chunk_text utility."""

    def test_short_text_single_chunk(self):
        text = "word " * 100
        chunks = chunk_text(text.strip(), chunk_size=512, chunk_overlap=64)
        assert len(chunks) == 1

    def test_exact_chunk_size(self):
        text = " ".join(f"w{i}" for i in range(512))
        chunks = chunk_text(text, chunk_size=512, chunk_overlap=64)
        assert len(chunks) == 1

    def test_two_chunks_with_overlap(self):
        # 600 words with chunk_size=512 and overlap=64 -> step=448
        # chunk 0: words[0:512], chunk 1: words[448:600]
        text = " ".join(f"w{i}" for i in range(600))
        chunks = chunk_text(text, chunk_size=512, chunk_overlap=64)
        assert len(chunks) == 2
        # Check overlap: last 64 words of chunk 0 == first 64 words of chunk 1
        words_0 = chunks[0].split()
        words_1 = chunks[1].split()
        assert words_0[-64:] == words_1[:64]

    def test_many_chunks(self):
        # 2048 words, step=448 -> ceil(2048/448) = 5 chunks
        text = " ".join(f"w{i}" for i in range(2048))
        chunks = chunk_text(text, chunk_size=512, chunk_overlap=64)
        assert len(chunks) >= 4

    def test_empty_text(self):
        assert chunk_text("", chunk_size=512, chunk_overlap=64) == []

    def test_whitespace_only(self):
        assert chunk_text("   \n\t  ", chunk_size=512, chunk_overlap=64) == []

    def test_overlap_must_be_less_than_size(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            chunk_text("some text", chunk_size=10, chunk_overlap=10)

    def test_overlap_greater_than_size_raises(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            chunk_text("some text", chunk_size=10, chunk_overlap=15)

    def test_all_words_covered(self):
        """Every word in the input must appear in at least one chunk."""
        words = [f"w{i}" for i in range(1000)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=512, chunk_overlap=64)
        covered = set()
        for chunk in chunks:
            covered.update(chunk.split())
        assert set(words) == covered


# =============================================================================
# IngestionService tests
# =============================================================================


@pytest.fixture
def ingestion_service(
    embeddings: FakeEmbeddings,
    store: InMemoryVectorStore,
) -> IngestionService:
    return IngestionService(
        embeddings=embeddings,
        vector_store=store,
        chunking=ChunkingConfig(chunk_size=50, chunk_overlap=10),
    )


class TestIngestionService:
    """Integration tests for the ingestion pipeline."""

    async def test_ingest_short_text(
        self,
        ingestion_service: IngestionService,
        store: InMemoryVectorStore,
    ):
        result = await ingestion_service.ingest(
            text="This is a short test document.",
            material_id="mat-001",
        )
        assert result.material_id == "mat-001"
        assert result.chunk_count == 1
        assert len(result.chunk_ids) == 1
        assert store.count == 1

    async def test_ingest_generates_material_id(
        self,
        ingestion_service: IngestionService,
    ):
        result = await ingestion_service.ingest(text="auto id test")
        assert result.material_id  # non-empty
        assert len(result.material_id) > 0

    async def test_ingest_multiple_chunks(
        self,
        ingestion_service: IngestionService,
        store: InMemoryVectorStore,
    ):
        text = " ".join(f"word{i}" for i in range(200))
        result = await ingestion_service.ingest(
            text=text,
            material_id="mat-multi",
        )
        assert result.chunk_count > 1
        assert store.count == result.chunk_count

    async def test_ingest_metadata_propagated(
        self,
        ingestion_service: IngestionService,
        store: InMemoryVectorStore,
        embeddings: FakeEmbeddings,
    ):
        await ingestion_service.ingest(
            text="metadata test content here",
            material_id="mat-meta",
            metadata={"teacher_id": "teacher-42", "subject": "math"},
        )
        # Search for the chunk and verify metadata
        query_vec = await embeddings.embed_text("metadata test content here")
        results = await store.search(query_embedding=query_vec, k=1)
        assert len(results) == 1
        assert results[0].metadata["teacher_id"] == "teacher-42"
        assert results[0].metadata["subject"] == "math"
        assert results[0].metadata["material_id"] == "mat-meta"
        assert "chunk_index" in results[0].metadata

    async def test_ingest_empty_text(
        self,
        ingestion_service: IngestionService,
        store: InMemoryVectorStore,
    ):
        result = await ingestion_service.ingest(text="", material_id="mat-empty")
        assert result.chunk_count == 0
        assert result.chunk_ids == []
        assert store.count == 0

    async def test_ingest_chunk_ids_format(
        self,
        ingestion_service: IngestionService,
    ):
        result = await ingestion_service.ingest(
            text="short text",
            material_id="mat-fmt",
        )
        assert result.chunk_ids[0] == "mat-fmt__chunk_0000"

    async def test_ingest_idempotent(
        self,
        ingestion_service: IngestionService,
        store: InMemoryVectorStore,
    ):
        """Re-ingesting the same material overwrites, does not duplicate."""
        text = "idempotency test document content"
        await ingestion_service.ingest(text=text, material_id="mat-idem")
        await ingestion_service.ingest(text=text, material_id="mat-idem")
        assert store.count == 1  # same IDs, upsert semantics


# =============================================================================
# RAGService tests
# =============================================================================


@pytest.fixture
async def populated_store(
    embeddings: FakeEmbeddings,
    store: InMemoryVectorStore,
) -> InMemoryVectorStore:
    """Store pre-populated with a few documents for RAG tests."""
    ingestion = IngestionService(
        embeddings=embeddings,
        vector_store=store,
        chunking=ChunkingConfig(chunk_size=50, chunk_overlap=10),
    )

    await ingestion.ingest(
        text="Photosynthesis is the process by which plants convert light into energy",
        material_id="bio-001",
        metadata={"teacher_id": "t1", "subject": "biology"},
    )
    await ingestion.ingest(
        text="The quadratic formula solves second degree polynomial equations",
        material_id="math-001",
        metadata={"teacher_id": "t1", "subject": "math"},
    )
    await ingestion.ingest(
        text="World War II ended in 1945 after the surrender of Germany and Japan",
        material_id="hist-001",
        metadata={"teacher_id": "t2", "subject": "history"},
    )

    return store


@pytest.fixture
def rag_service(
    embeddings: FakeEmbeddings,
    populated_store: InMemoryVectorStore,
) -> RAGService:
    return RAGService(
        embeddings=embeddings,
        vector_store=populated_store,
        default_k=5,
        similarity_threshold=0.0,  # low threshold for testing
    )


class TestRAGService:
    """Integration tests for the RAG query service."""

    async def test_query_returns_results(self, rag_service: RAGService):
        result = await rag_service.query(text="photosynthesis in plants")
        assert len(result.results) > 0
        assert result.query == "photosynthesis in plants"

    async def test_query_respects_k(self, rag_service: RAGService):
        result = await rag_service.query(text="test query", k=1)
        assert len(result.results) <= 1

    async def test_query_with_filters(self, rag_service: RAGService):
        result = await rag_service.query(
            text="any query",
            filters={"teacher_id": "t1"},
        )
        for r in result.results:
            assert r.metadata["teacher_id"] == "t1"

    async def test_query_with_subject_filter(self, rag_service: RAGService):
        result = await rag_service.query(
            text="any query",
            filters={"subject": "history"},
        )
        for r in result.results:
            assert r.metadata["subject"] == "history"

    async def test_query_threshold_filters_low_scores(
        self,
        embeddings: FakeEmbeddings,
        populated_store: InMemoryVectorStore,
    ):
        """With a high threshold, results with low similarity are excluded."""
        service = RAGService(
            embeddings=embeddings,
            vector_store=populated_store,
            similarity_threshold=0.999,  # extremely high
        )
        result = await service.query(text="random unrelated text xyz")
        # The threshold should filter out most/all results
        assert result.total_candidates >= 0
        # All returned results must be above threshold
        for r in result.results:
            assert r.score >= 0.999

    async def test_query_override_threshold(self, rag_service: RAGService):
        """similarity_threshold parameter overrides the default."""
        result = await rag_service.query(
            text="test",
            similarity_threshold=0.999,
        )
        for r in result.results:
            assert r.score >= 0.999

    async def test_query_total_candidates_tracked(self, rag_service: RAGService):
        result = await rag_service.query(text="some query")
        assert result.total_candidates >= len(result.results)

    async def test_query_results_sorted_by_score(self, rag_service: RAGService):
        result = await rag_service.query(text="test", k=10)
        scores = [r.score for r in result.results]
        assert scores == sorted(scores, reverse=True)

    async def test_query_empty_store(
        self,
        embeddings: FakeEmbeddings,
    ):
        empty_store = InMemoryVectorStore()
        service = RAGService(
            embeddings=embeddings,
            vector_store=empty_store,
        )
        result = await service.query(text="anything")
        assert result.results == []
        assert result.total_candidates == 0

    async def test_query_result_has_source_attribution(self, rag_service: RAGService):
        """Each result should carry metadata with material_id for attribution."""
        result = await rag_service.query(text="test", k=10)
        for r in result.results:
            assert "material_id" in r.metadata

    async def test_query_filters_combined_with_threshold(
        self,
        embeddings: FakeEmbeddings,
        populated_store: InMemoryVectorStore,
    ):
        service = RAGService(
            embeddings=embeddings,
            vector_store=populated_store,
            similarity_threshold=0.0,
        )
        result = await service.query(
            text="anything",
            filters={"teacher_id": "t2"},
            similarity_threshold=0.0,
        )
        # Only t2's documents should appear
        for r in result.results:
            assert r.metadata["teacher_id"] == "t2"
