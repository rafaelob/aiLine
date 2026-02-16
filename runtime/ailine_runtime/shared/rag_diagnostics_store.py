"""In-memory store for RAG diagnostics reports.

Stores per-run RAG diagnostics with automatic TTL eviction.
Mirrors the TraceStore pattern for consistency.
"""

from __future__ import annotations

import asyncio
import time

from ..domain.entities.rag_diagnostics import RAGDiagnostics

_DEFAULT_TTL_SECONDS = 3600
_MAX_ENTRIES = 200


class RAGDiagnosticsStore:
    """In-memory store for RAG diagnostics keyed by run_id."""

    def __init__(
        self,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
        max_entries: int = _MAX_ENTRIES,
    ) -> None:
        self._store: dict[str, RAGDiagnostics] = {}
        self._timestamps: dict[str, float] = {}
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._lock = asyncio.Lock()

    async def save(self, diagnostics: RAGDiagnostics) -> None:
        """Save or update diagnostics for a run_id."""
        async with self._lock:
            self._evict_expired()
            self._store[diagnostics.run_id] = diagnostics
            self._timestamps[diagnostics.run_id] = time.monotonic()
            self._enforce_capacity()

    async def get(
        self, run_id: str, *, teacher_id: str | None = None
    ) -> RAGDiagnostics | None:
        """Get diagnostics by run_id, or None if not found/expired.

        When *teacher_id* is provided, only returns the diagnostics if
        it belongs to the given teacher (tenant isolation).
        """
        async with self._lock:
            self._evict_expired()
            diag = self._store.get(run_id)
            if diag is None:
                return None
            if (
                teacher_id is not None
                and diag.teacher_id
                and diag.teacher_id != teacher_id
            ):
                return None
            return diag

    async def list_recent(
        self, limit: int = 20, *, teacher_id: str | None = None
    ) -> list[RAGDiagnostics]:
        """List recent diagnostics, newest first.

        When *teacher_id* is provided, only returns diagnostics belonging
        to that teacher (tenant isolation).
        """
        async with self._lock:
            self._evict_expired()
            items = sorted(
                self._store.items(),
                key=lambda kv: self._timestamps.get(kv[0], 0),
                reverse=True,
            )
            results: list[RAGDiagnostics] = []
            for _, v in items:
                if (
                    teacher_id is not None
                    and v.teacher_id
                    and v.teacher_id != teacher_id
                ):
                    continue
                results.append(v)
                if len(results) >= limit:
                    break
            return results

    def _evict_expired(self) -> None:
        now = time.monotonic()
        expired = [k for k, ts in self._timestamps.items() if now - ts > self._ttl]
        for k in expired:
            self._store.pop(k, None)
            self._timestamps.pop(k, None)

    def _enforce_capacity(self) -> None:
        while len(self._store) > self._max_entries:
            oldest = min(self._timestamps, key=lambda k: self._timestamps[k])
            self._store.pop(oldest, None)
            self._timestamps.pop(oldest, None)


# Singleton instance
_store: RAGDiagnosticsStore | None = None


def get_rag_diagnostics_store() -> RAGDiagnosticsStore:
    """Get the global RAG diagnostics store singleton."""
    global _store
    if _store is None:
        _store = RAGDiagnosticsStore()
    return _store
