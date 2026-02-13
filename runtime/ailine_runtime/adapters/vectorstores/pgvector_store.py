"""pgvector VectorStore adapter using SQLAlchemy async.

Uses the ``<=>`` cosine distance operator and an HNSW index for
approximate nearest-neighbor search.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.ports.vectorstore import VectorSearchResult
from ...shared.observability import get_logger

_log = get_logger("ailine.adapters.vectorstores.pgvector")

# Strict SQL identifier pattern to prevent injection via table name (FINDING-SEC-1).
_VALID_IDENT = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class PgVectorStore:
    """VectorStore backed by PostgreSQL + pgvector.

    Args:
        session_factory: An async callable that returns an ``AsyncSession``
            (typically a ``sessionmaker`` or async context manager).
        table_name: Name of the chunks table. Must be a valid SQL identifier.
        dimensions: Embedding vector length (must match the column width).

    Graceful degradation:
        When PostgreSQL is unreachable, all query/upsert methods raise
        ``SQLAlchemy`` connection errors. The Container handles this by
        returning ``None`` for the vectorstore port when the DB URL is
        not configured or points to SQLite, so callers should check for
        ``container.vectorstore is None`` before attempting vector ops.
        The readiness probe (``/health/ready``) reports ``"error"`` status
        when the database connection fails, allowing load balancers to
        route traffic away from unhealthy instances.
    """

    def __init__(
        self,
        session_factory: Callable[..., AsyncSession],
        *,
        table_name: str = "chunks",
        dimensions: int = 1536,
    ) -> None:
        if not _VALID_IDENT.match(table_name):
            raise ValueError(f"Invalid table_name: {table_name!r} (must be a valid SQL identifier)")
        if not (1 <= dimensions <= 4000):
            raise ValueError(f"Invalid dimensions: {dimensions} (must be 1..4000)")
        self._session_factory = session_factory
        self._table = table_name
        self._dimensions = dimensions

    # -- DDL helpers (run once at startup or via migration) --------------------

    async def ensure_table(self) -> None:
        """Create the chunks table and HNSW index if they do not exist.

        Intended for development bootstrapping.  Production should use
        Alembic migrations instead.
        """
        async with self._session_factory() as session:
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await session.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._table} (
                        id          TEXT PRIMARY KEY,
                        embedding   vector({self._dimensions}) NOT NULL,
                        content     TEXT NOT NULL DEFAULT '',
                        metadata    JSONB NOT NULL DEFAULT '{{}}'::jsonb
                    )
                    """
                )
            )
            # HNSW index for cosine distance
            idx_name = f"idx_{self._table}_embedding_hnsw"
            await session.execute(
                text(
                    f"""
                    CREATE INDEX IF NOT EXISTS {idx_name}
                        ON {self._table}
                        USING hnsw (embedding vector_cosine_ops)
                        WITH (m = 16, ef_construction = 128)
                    """
                )
            )
            await session.commit()
        _log.info("ensure_table_done", table=self._table)

    # -- Protocol methods -----------------------------------------------------

    async def upsert(
        self,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Insert or update chunks.

        Uses ``INSERT ... ON CONFLICT DO UPDATE`` for idempotency.
        """
        if not ids:
            return

        n = len(ids)
        if not (len(embeddings) == len(texts) == len(metadatas) == n):
            raise ValueError(
                f"upsert expects ids/embeddings/texts/metadatas with same length "
                f"(got {n}/{len(embeddings)}/{len(texts)}/{len(metadatas)})"
            )

        _log.debug("upsert", table=self._table, count=n)

        stmt = text(
            f"""
            INSERT INTO {self._table} (id, embedding, content, metadata)
            VALUES (:id, :embedding, :content, :metadata)
            ON CONFLICT (id) DO UPDATE SET
                embedding = EXCLUDED.embedding,
                content   = EXCLUDED.content,
                metadata  = EXCLUDED.metadata
            """
        )

        # Batch all rows into a single executemany call to avoid N+1 round-trips
        params_list = [
            {
                "id": ids[i],
                "embedding": "[" + ",".join(str(v) for v in embeddings[i]) + "]",
                "content": texts[i],
                "metadata": _json_dumps(metadatas[i]),
            }
            for i in range(len(ids))
        ]

        async with self._session_factory() as session:
            await session.execute(stmt, params_list)
            await session.commit()

    async def search(
        self,
        *,
        query_embedding: list[float],
        k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search for the *k* most similar chunks using cosine distance.

        Cosine distance ``<=>`` ranges from 0 (identical) to 2 (opposite).
        We convert it to a similarity score: ``1 - distance``.

        Args:
            query_embedding: The query vector.
            k: Maximum number of results.
            filters: Optional metadata filters.  Keys are matched with
                equality against the ``metadata`` JSONB column using
                ``metadata @> :filter_json``.

        Returns:
            List of ``VectorSearchResult`` ordered by descending similarity.
        """
        vec_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        where_clause = ""
        params: dict[str, Any] = {
            "query_vec": vec_str,
            "k": k,
        }

        if filters:
            where_clause = "WHERE metadata @> :filter_json::jsonb"
            params["filter_json"] = _json_dumps(filters)

        query = text(
            f"""
            SELECT id,
                   1 - (embedding <=> :query_vec::vector) AS score,
                   content,
                   metadata
            FROM {self._table}
            {where_clause}
            ORDER BY embedding <=> :query_vec::vector
            LIMIT :k
            """
        )

        _log.debug("search", table=self._table, k=k, filters=filters)

        async with self._session_factory() as session:
            result = await session.execute(query, params)
            rows = result.fetchall()

        return [
            VectorSearchResult(
                id=row[0],
                score=float(row[1]),
                text=row[2],
                metadata=row[3] if isinstance(row[3], dict) else _json_loads(row[3]),
            )
            for row in rows
        ]

    async def delete(self, *, ids: list[str]) -> None:
        """Delete chunks by their IDs."""
        if not ids:
            return

        _log.debug("delete", table=self._table, count=len(ids))

        # Use ANY(:ids) for batch deletion
        stmt = text(f"DELETE FROM {self._table} WHERE id = ANY(:ids)")

        async with self._session_factory() as session:
            await session.execute(stmt, {"ids": ids})
            await session.commit()


# -- JSON helpers (avoid import-time dependency on psycopg/asyncpg) -----------


def _json_dumps(obj: Any) -> str:
    """Serialize to JSON string."""
    import json

    return json.dumps(obj, ensure_ascii=False, default=str)


def _json_loads(raw: str | bytes) -> dict[str, Any]:
    """Deserialize JSON string."""
    import json

    result: dict[str, Any] = json.loads(raw)
    return result
