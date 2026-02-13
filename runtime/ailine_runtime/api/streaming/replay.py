"""SSE event replay store backed by Redis Sorted Sets (ADR-054).

Stores the last N events per run_id in a Redis ZSET (score = seq).
On reconnection with Last-Event-ID, replays missed events.

When Redis is unavailable, falls back to an in-memory store
(suitable for single-instance dev/test).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayConfig:
    """Configuration for the SSE replay store."""

    ttl_seconds: int = 30 * 60  # 30 minutes
    keep_last: int = 100
    prefix: str = "runs"


class InMemoryReplayStore:
    """In-memory replay store for single-instance dev/test.

    Uses a dict of lists, trimmed to keep_last entries.
    No TTL enforcement (entries persist until process restart).
    """

    def __init__(self, config: ReplayConfig | None = None) -> None:
        self._config = config or ReplayConfig()
        self._store: dict[str, list[tuple[int, str]]] = defaultdict(list)

    async def append(self, run_id: str, seq: int, payload: str) -> None:
        """Append an event to the replay buffer."""
        entries = self._store[run_id]
        entries.append((seq, payload))
        # Trim to keep_last
        if len(entries) > self._config.keep_last:
            self._store[run_id] = entries[-self._config.keep_last :]

    async def replay(
        self, run_id: str, after_seq: int | None = None
    ) -> list[tuple[int, str]]:
        """Replay events after the given sequence number.

        Args:
            run_id: The run to replay events for.
            after_seq: If provided, return events with seq > after_seq.
                       If None, return the last keep_last events.

        Returns:
            List of (seq, payload_json) tuples in ascending order.
        """
        entries = self._store.get(run_id, [])
        if after_seq is not None:
            return [(s, p) for s, p in entries if s > after_seq]
        return list(entries)

    async def mark_terminal(self, run_id: str, terminal_type: str) -> bool:
        """Mark a run as terminated. Returns True if this was the first terminal marker."""
        key = f"_terminal:{run_id}"
        if key in self._store:
            return False
        self._store[key] = [(0, terminal_type)]
        return True

    async def is_terminal(self, run_id: str) -> bool:
        """Check if a run has been marked as terminal."""
        return f"_terminal:{run_id}" in self._store


class RedisReplayStore:
    """Redis-backed replay store using Sorted Sets (ADR-054).

    ZSET key: {prefix}:{run_id}:events (score = seq, member = "{seq}|{payload}")
    Terminal key: {prefix}:{run_id}:terminal (SET NX EX)
    Seq counter: {prefix}:{run_id}:seq (INCR)
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        config: ReplayConfig | None = None,
    ) -> None:
        from redis.asyncio import Redis

        self._redis: Redis = Redis.from_url(redis_url, decode_responses=True)
        self._config = config or ReplayConfig()
        self._prefix = self._config.prefix

    def _events_key(self, run_id: str) -> str:
        return f"{self._prefix}:{run_id}:events"

    def _seq_key(self, run_id: str) -> str:
        return f"{self._prefix}:{run_id}:seq"

    def _terminal_key(self, run_id: str) -> str:
        return f"{self._prefix}:{run_id}:terminal"

    async def next_seq(self, run_id: str) -> int:
        """Get the next sequence number via Redis INCR."""
        return int(await self._redis.incr(self._seq_key(run_id)))

    async def append(self, run_id: str, seq: int, payload: str) -> None:
        """Append an event to the ZSET replay buffer."""
        key = self._events_key(run_id)
        # Member includes seq for uniqueness: "{seq}|{payload}"
        member = f"{seq}|{payload}"

        pipe = self._redis.pipeline(transaction=True)
        pipe.zadd(key, {member: float(seq)})
        # Trim: keep only last N by removing lowest scores
        pipe.zremrangebyrank(key, 0, -(self._config.keep_last + 1))
        pipe.expire(key, self._config.ttl_seconds)
        pipe.expire(self._seq_key(run_id), self._config.ttl_seconds)
        await pipe.execute()

    async def replay(
        self, run_id: str, after_seq: int | None = None
    ) -> list[tuple[int, str]]:
        """Replay events from Redis ZSET."""
        key = self._events_key(run_id)

        if after_seq is not None:
            items = await self._redis.zrangebyscore(
                key, min=f"({after_seq}", max="+inf", withscores=True
            )
        else:
            items = await self._redis.zrange(
                key, 0, -1, withscores=True
            )

        result: list[tuple[int, str]] = []
        for member, score in items:
            seq = int(score)
            # Extract payload from "{seq}|{payload}" format
            payload = member.split("|", 1)[1] if "|" in member else member
            result.append((seq, payload))
        return result

    async def mark_terminal(self, run_id: str, terminal_type: str) -> bool:
        """Atomically mark a run as terminated (SET NX EX)."""
        return bool(
            await self._redis.set(
                self._terminal_key(run_id),
                terminal_type,
                nx=True,
                ex=self._config.ttl_seconds,
            )
        )

    async def is_terminal(self, run_id: str) -> bool:
        """Check if a run has been marked as terminal."""
        result = await self._redis.exists(self._terminal_key(run_id))
        return int(result) > 0

    async def close(self) -> None:
        """Close the Redis connection."""
        await self._redis.close()
