"""Tests for pgvector VectorStore adapter.

Mocks SQLAlchemy AsyncSession to test operations without a real database.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from ailine_runtime.adapters.vectorstores.pgvector_store import (
    PgVectorStore,
    _json_dumps,
    _json_loads,
)


@asynccontextmanager
async def _mock_session_ctx(mock_session):
    """AsyncContextManager that yields the mock session."""
    yield mock_session


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def session_factory(mock_session):
    """Return a callable that produces an async context manager yielding mock_session."""
    def factory():
        return _mock_session_ctx(mock_session)
    return factory


@pytest.fixture
def store(session_factory):
    return PgVectorStore(session_factory, table_name="test_chunks", dimensions=4)


class TestPgVectorStoreEnsureTable:
    @pytest.mark.asyncio
    async def test_ensure_table_creates_extension_and_table(self, store, mock_session):
        await store.ensure_table()
        # Should have executed 3 statements: CREATE EXTENSION, CREATE TABLE, CREATE INDEX
        assert mock_session.execute.call_count == 3
        assert mock_session.commit.call_count == 1


class TestPgVectorStoreUpsert:
    @pytest.mark.asyncio
    async def test_upsert_empty_noop(self, store, mock_session):
        await store.upsert(ids=[], embeddings=[], texts=[], metadatas=[])
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_inserts_rows(self, store, mock_session):
        await store.upsert(
            ids=["a", "b"],
            embeddings=[[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]],
            texts=["hello", "world"],
            metadatas=[{"k": "v"}, {"n": 1}],
        )
        assert mock_session.execute.call_count == 2
        mock_session.commit.assert_called_once()


class TestPgVectorStoreSearch:
    @pytest.mark.asyncio
    async def test_search_without_filters(self, store, mock_session):
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, i: ["id1", 0.85, "content", {"k": "v"}][i]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        results = await store.search(query_embedding=[0.1, 0.2, 0.3, 0.4], k=5)
        assert len(results) == 1
        assert results[0].id == "id1"
        assert results[0].score == 0.85
        assert results[0].text == "content"
        assert results[0].metadata == {"k": "v"}

    @pytest.mark.asyncio
    async def test_search_with_filters(self, store, mock_session):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        results = await store.search(
            query_embedding=[0.1, 0.2, 0.3, 0.4],
            k=3,
            filters={"subject": "math"},
        )
        assert results == []
        # Verify the WHERE clause was included
        call_args = mock_session.execute.call_args
        str(call_args[0][0])
        assert "filter_json" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_search_json_metadata_parsing(self, store, mock_session):
        """When metadata is a JSON string instead of dict, it should be parsed."""
        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, i: ["id1", 0.9, "text", '{"k": "v"}'][i]
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        results = await store.search(query_embedding=[0.1, 0.2, 0.3, 0.4], k=1)
        assert results[0].metadata == {"k": "v"}


class TestPgVectorStoreDelete:
    @pytest.mark.asyncio
    async def test_delete_empty_noop(self, store, mock_session):
        await store.delete(ids=[])
        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_with_ids(self, store, mock_session):
        await store.delete(ids=["id1", "id2"])
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestJsonHelpers:
    def test_json_dumps(self):
        result = _json_dumps({"key": "value", "nested": [1, 2]})
        assert '"key"' in result
        assert '"nested"' in result

    def test_json_loads(self):
        result = _json_loads('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_loads_bytes(self):
        result = _json_loads(b'{"key": "value"}')
        assert result == {"key": "value"}
