"""In-memory trace store for pipeline run traces.

Stores RunTrace objects keyed by run_id with automatic TTL eviction.
Thread-safe for concurrent async access.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

from ..domain.entities.trace import NodeTrace, RunTrace

logger = logging.getLogger("ailine.shared.trace_store")

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

    async def get(
        self, run_id: str, *, teacher_id: str
    ) -> RunTrace | None:
        """Get a trace by run_id, or None if not found / expired.

        Only returns the trace if it belongs to the given teacher
        (tenant isolation). *teacher_id* is required.
        """
        async with self._lock:
            self._evict_expired()
            trace = self._traces.get(run_id)
            if trace is None:
                return None
            if trace.teacher_id != teacher_id:
                return None
            return trace

    async def get_or_create(self, run_id: str, *, teacher_id: str = "") -> RunTrace:
        """Get existing trace or create a new empty one.

        When *teacher_id* is provided, it is stored on the trace for
        tenant isolation filtering in subsequent lookups.
        """
        async with self._lock:
            self._evict_expired()
            if run_id not in self._traces:
                self._traces[run_id] = RunTrace(
                    run_id=run_id,
                    teacher_id=teacher_id,
                    created_at=datetime.now(UTC).isoformat(),
                )
                self._timestamps[run_id] = time.monotonic()
                self._enforce_capacity()
            elif teacher_id and not self._traces[run_id].teacher_id:
                self._traces[run_id].teacher_id = teacher_id
            return self._traces[run_id]

    async def append_node(
        self, run_id: str, node: NodeTrace, *, teacher_id: str = ""
    ) -> None:
        """Append a node trace to a run.

        F-252: Does NOT auto-create a RunTrace.  If the run_id does not
        exist (i.e. was never initialised via ``get_or_create``), the
        call is silently ignored with a warning log.  This prevents
        tenant-integrity bypass through implicit trace creation.

        When *teacher_id* is provided, validates it matches the stored
        trace (tenant isolation).
        """
        async with self._lock:
            if run_id not in self._traces:
                logger.warning(
                    "append_node called for non-existent run_id=%s — ignored",
                    run_id,
                )
                return
            trace = self._traces[run_id]
            if teacher_id and trace.teacher_id and trace.teacher_id != teacher_id:
                logger.warning(
                    "append_node tenant mismatch run_id=%s expected=%s got=%s — ignored",
                    run_id,
                    trace.teacher_id,
                    teacher_id,
                )
                return
            trace.nodes.append(node)
            self._timestamps[run_id] = time.monotonic()

    async def update_run(
        self, run_id: str, *, teacher_id: str = "", **kwargs: Any
    ) -> None:
        """Update top-level run fields (status, total_time_ms, etc.).

        F-252: Does NOT auto-create a RunTrace.  If the run_id does not
        exist, the call is silently ignored with a warning log.

        When *teacher_id* is provided, validates it matches the stored
        trace (tenant isolation).
        """
        async with self._lock:
            if run_id not in self._traces:
                logger.warning(
                    "update_run called for non-existent run_id=%s — ignored",
                    run_id,
                )
                return
            trace = self._traces[run_id]
            if teacher_id and trace.teacher_id and trace.teacher_id != teacher_id:
                logger.warning(
                    "update_run tenant mismatch run_id=%s expected=%s got=%s — ignored",
                    run_id,
                    trace.teacher_id,
                    teacher_id,
                )
                return
            for key, value in kwargs.items():
                if hasattr(trace, key):
                    setattr(trace, key, value)
            self._timestamps[run_id] = time.monotonic()

    async def list_recent(
        self,
        limit: int = 20,
        *,
        teacher_id: str | None = None,
        status: str | None = None,
    ) -> list[RunTrace]:
        """List recent traces, newest first.

        When *teacher_id* is provided, only returns traces belonging to
        that teacher (tenant isolation).
        When *status* is provided, only returns traces with that status
        (F-259: server-side filtering).
        """
        async with self._lock:
            self._evict_expired()
            sorted_ids = sorted(
                self._timestamps.keys(),
                key=lambda rid: self._timestamps[rid],
                reverse=True,
            )
            traces: list[RunTrace] = []
            for rid in sorted_ids:
                t = self._traces[rid]
                if teacher_id is not None and t.teacher_id != teacher_id:
                    continue
                if status is not None and t.status != status:
                    continue
                traces.append(t)
                if len(traces) >= limit:
                    break
            return traces

    def _evict_expired(self) -> None:
        """Remove entries older than TTL (call under lock)."""
        now = time.monotonic()
        expired = [rid for rid, ts in self._timestamps.items() if now - ts > self._ttl]
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
_store_lock = __import__("threading").Lock()


def get_trace_store() -> TraceStore:
    """Get or create the singleton trace store."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = TraceStore()
    return _store


def reset_trace_store() -> None:
    """Reset the singleton (for testing)."""
    global _store
    _store = None
