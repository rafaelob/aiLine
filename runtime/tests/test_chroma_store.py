"""Tests for ChromaDB VectorStore adapter.

Mocks chromadb to test CRUD operations without the real dependency.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_chromadb():
    """Create a mock chromadb module with EphemeralClient and PersistentClient."""
    mock_collection = MagicMock()
    mock_collection.name = "chunks"

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    mock_module = MagicMock()
    mock_module.EphemeralClient.return_value = mock_client
    mock_module.PersistentClient.return_value = mock_client

    return mock_module, mock_client, mock_collection


class TestChromaVectorStoreInit:
    def test_ephemeral_mode(self, mock_chromadb):
        mock_module, mock_client, _ = mock_chromadb
        with patch.dict("sys.modules", {"chromadb": mock_module}):
            from ailine_runtime.adapters.vectorstores.chroma_store import ChromaVectorStore

            ChromaVectorStore(collection_name="test_chunks")
            mock_module.EphemeralClient.assert_called_once()
            mock_client.get_or_create_collection.assert_called_once_with(
                name="test_chunks",
                metadata={"hnsw:space": "cosine"},
            )

    def test_persistent_mode(self, mock_chromadb):
        mock_module, _mock_client, _ = mock_chromadb
        with patch.dict("sys.modules", {"chromadb": mock_module}):
            from ailine_runtime.adapters.vectorstores.chroma_store import ChromaVectorStore

            ChromaVectorStore(
                collection_name="test_chunks",
                persist_directory="/tmp/chroma",
            )
            mock_module.PersistentClient.assert_called_once_with(path="/tmp/chroma")


class TestChromaVectorStoreUpsert:
    @pytest.mark.asyncio
    async def test_upsert_empty_ids_noop(self, mock_chromadb):
        mock_module, _, mock_collection = mock_chromadb
        with patch.dict("sys.modules", {"chromadb": mock_module}):
            from ailine_runtime.adapters.vectorstores.chroma_store import ChromaVectorStore

            store = ChromaVectorStore()
            await store.upsert(ids=[], embeddings=[], texts=[], metadatas=[])
            mock_collection.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_with_data(self, mock_chromadb):
        mock_module, _, mock_collection = mock_chromadb
        with patch.dict("sys.modules", {"chromadb": mock_module}):
            from ailine_runtime.adapters.vectorstores.chroma_store import ChromaVectorStore

            store = ChromaVectorStore()
            await store.upsert(
                ids=["id1", "id2"],
                embeddings=[[0.1, 0.2], [0.3, 0.4]],
                texts=["hello", "world"],
                metadatas=[{"key": "val"}, {"nested": {"a": 1}}],
            )
            mock_collection.upsert.assert_called_once()
            call_kwargs = mock_collection.upsert.call_args
            assert call_kwargs.kwargs["ids"] == ["id1", "id2"]
            # Nested metadata should be JSON-serialized
            metas = call_kwargs.kwargs["metadatas"]
            assert metas[0]["key"] == "val"
            assert isinstance(metas[1]["nested"], str)  # JSON-dumped


class TestChromaVectorStoreSearch:
    @pytest.mark.asyncio
    async def test_search_returns_results(self, mock_chromadb):
        mock_module, _, mock_collection = mock_chromadb
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.3]],
            "documents": [["text one", "text two"]],
            "metadatas": [[{"k": "v1"}, {"k": "v2"}]],
        }
        with patch.dict("sys.modules", {"chromadb": mock_module}):
            from ailine_runtime.adapters.vectorstores.chroma_store import ChromaVectorStore

            store = ChromaVectorStore()
            results = await store.search(query_embedding=[0.1, 0.2], k=2)
            assert len(results) == 2
            assert results[0].id == "id1"
            assert results[0].score == pytest.approx(0.9)
            assert results[0].text == "text one"
            assert results[1].score == pytest.approx(0.7)

    @pytest.mark.asyncio
    async def test_search_empty_results(self, mock_chromadb):
        mock_module, _, mock_collection = mock_chromadb
        mock_collection.query.return_value = {
            "ids": [[]],
            "distances": [[]],
            "documents": [[]],
            "metadatas": [[]],
        }
        with patch.dict("sys.modules", {"chromadb": mock_module}):
            from ailine_runtime.adapters.vectorstores.chroma_store import ChromaVectorStore

            store = ChromaVectorStore()
            results = await store.search(query_embedding=[0.1], k=5)
            assert results == []

    @pytest.mark.asyncio
    async def test_search_with_filters(self, mock_chromadb):
        mock_module, _, mock_collection = mock_chromadb
        mock_collection.query.return_value = {
            "ids": [["id1"]],
            "distances": [[0.05]],
            "documents": [["filtered"]],
            "metadatas": [[{"subject": "math"}]],
        }
        with patch.dict("sys.modules", {"chromadb": mock_module}):
            from ailine_runtime.adapters.vectorstores.chroma_store import ChromaVectorStore

            store = ChromaVectorStore()
            results = await store.search(query_embedding=[0.1], k=1, filters={"subject": "math"})
            assert len(results) == 1
            call_kwargs = mock_collection.query.call_args
            assert call_kwargs.kwargs["where"] == {"subject": "math"}

    @pytest.mark.asyncio
    async def test_search_missing_optional_fields(self, mock_chromadb):
        """Edge case: distances/documents/metadatas might be None-ish."""
        mock_module, _, mock_collection = mock_chromadb
        mock_collection.query.return_value = {
            "ids": [["id1"]],
            "distances": None,
            "documents": None,
            "metadatas": None,
        }
        with patch.dict("sys.modules", {"chromadb": mock_module}):
            from ailine_runtime.adapters.vectorstores.chroma_store import ChromaVectorStore

            store = ChromaVectorStore()
            results = await store.search(query_embedding=[0.1], k=1)
            assert len(results) == 1
            assert results[0].score == 1.0  # 1 - 0.0
            assert results[0].text == ""
            assert results[0].metadata == {}


class TestChromaVectorStoreDelete:
    @pytest.mark.asyncio
    async def test_delete_empty_noop(self, mock_chromadb):
        mock_module, _, mock_collection = mock_chromadb
        with patch.dict("sys.modules", {"chromadb": mock_module}):
            from ailine_runtime.adapters.vectorstores.chroma_store import ChromaVectorStore

            store = ChromaVectorStore()
            await store.delete(ids=[])
            mock_collection.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_with_ids(self, mock_chromadb):
        mock_module, _, mock_collection = mock_chromadb
        with patch.dict("sys.modules", {"chromadb": mock_module}):
            from ailine_runtime.adapters.vectorstores.chroma_store import ChromaVectorStore

            store = ChromaVectorStore()
            await store.delete(ids=["id1", "id2"])
            mock_collection.delete.assert_called_once_with(ids=["id1", "id2"])


class TestSanitizeMetadata:
    def test_primitives_pass_through(self):
        with patch.dict("sys.modules", {"chromadb": MagicMock()}):
            from ailine_runtime.adapters.vectorstores.chroma_store import _sanitize_metadata

            result = _sanitize_metadata({"s": "hello", "i": 42, "f": 3.14, "b": True})
            assert result == {"s": "hello", "i": 42, "f": 3.14, "b": True}

    def test_complex_values_serialized(self):
        with patch.dict("sys.modules", {"chromadb": MagicMock()}):
            from ailine_runtime.adapters.vectorstores.chroma_store import _sanitize_metadata

            result = _sanitize_metadata({"nested": {"a": [1, 2, 3]}})
            assert isinstance(result["nested"], str)
            assert "1" in result["nested"]
