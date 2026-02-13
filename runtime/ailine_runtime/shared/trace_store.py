"""In-memory trace store for pipeline run traces.

Stores RunTrace objects keyed by run_id with automatic TTL eviction.
Thread-safe for concurrent async access.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from ..domain.entities.trace import NodeTrace, RunTrace

# Default TTL: 1 hour
_DEFAULT_TTL_SECONDS = 3600
# Max entries to prevent unbounded growth
_MAX_ENTRIES = 500


class TraceStore:
    """In-memory store for pipeline run traces.

    Not persistent across restarts; suitable for MVP/demo.
    """

    def __init__(
        self,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
        max_entries: int = _MAX_ENTRIES,
    ) -> None:
        self._traces: dict[str, RunTrace] = {}
        self._timestamps: dict[str, float] = {}
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._lock = asyncio.Lock()

    async def get(self, run_id: str) -> RunTrace | None:
        """Get a trace by run_id, or None if not found / expired."""
        async with self._lock:
            self._evict_expired()
            return self._traces.get(run_id)

    async def get_or_create(self, run_id: str) -> RunTrace:
        """Get existing trace or create a new empty one."""
        async with self._lock:
            self._evict_expired()
            if run_id not in self._traces:
                self._traces[run_id] = RunTrace(run_id=run_id)
                self._timestamps[run_id] = time.monotonic()
                self._enforce_capacity()
            return self._traces[run_id]

    async def append_node(self, run_id: str, node: NodeTrace) -> None:
        """Append a node trace to a run."""
        async with self._lock:
            if run_id not in self._traces:
                self._traces[run_id] = RunTrace(run_id=run_id)
                self._timestamps[run_id] = time.monotonic()
            self._traces[run_id].nodes.append(node)
            self._timestamps[run_id] = time.monotonic()

    async def update_run(self, run_id: str, **kwargs: Any) -> None:
        """Update top-level run fields (status, total_time_ms, etc.)."""
        async with self._lock:
            if run_id not in self._traces:
                self._traces[run_id] = RunTrace(run_id=run_id)
                self._timestamps[run_id] = time.monotonic()
            trace = self._traces[run_id]
            for key, value in kwargs.items():
                if hasattr(trace, key):
                    setattr(trace, key, value)
            self._timestamps[run_id] = time.monotonic()

    async def list_recent(self, limit: int = 20) -> list[RunTrace]:
        """List recent traces, newest first."""
        async with self._lock:
            self._evict_expired()
            sorted_ids = sorted(
                self._timestamps.keys(),
                key=lambda rid: self._timestamps[rid],
                reverse=True,
            )
            return [self._traces[rid] for rid in sorted_ids[:limit]]

    def _evict_expired(self) -> None:
        """Remove entries older than TTL (call under lock)."""
        now = time.monotonic()
        expired = [
            rid for rid, ts in self._timestamps.items()
            if now - ts > self._ttl
        ]
        for rid in expired:
            del self._traces[rid]
            del self._timestamps[rid]

    def _enforce_capacity(self) -> None:
        """Evict oldest entries if over capacity (call under lock)."""
        while len(self._traces) > self._max_entries:
            oldest_id = min(self._timestamps, key=lambda k: self._timestamps[k])
            del self._traces[oldest_id]
            del self._timestamps[oldest_id]


# Module-level singleton
_store: TraceStore | None = None


def get_trace_store() -> TraceStore:
    """Get or create the singleton trace store."""
    global _store
    if _store is None:
        _store = TraceStore()
    return _store


def reset_trace_store() -> None:
    """Reset the singleton (for testing)."""
    global _store
    _store = None
