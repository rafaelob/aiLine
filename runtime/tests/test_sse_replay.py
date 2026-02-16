"""Tests for SSE event replay store (ADR-054)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ailine_runtime.api.streaming.replay import (
    InMemoryReplayStore,
    RedisReplayStore,
    ReplayConfig,
)


@pytest.fixture()
def store():
    return InMemoryReplayStore(ReplayConfig(keep_last=5, ttl_seconds=60))


class TestInMemoryReplayStore:
    @pytest.mark.asyncio
    async def test_append_and_replay_all(self, store):
        await store.append("run-1", 1, '{"type":"run.started"}')
        await store.append("run-1", 2, '{"type":"stage.started"}')
        await store.append("run-1", 3, '{"type":"stage.completed"}')

        events = await store.replay("run-1")
        assert len(events) == 3
        assert events[0] == (1, '{"type":"run.started"}')
        assert events[2] == (3, '{"type":"stage.completed"}')

    @pytest.mark.asyncio
    async def test_replay_after_seq(self, store):
        for i in range(1, 6):
            await store.append("run-1", i, f'{{"seq":{i}}}')

        events = await store.replay("run-1", after_seq=3)
        assert len(events) == 2
        assert events[0][0] == 4
        assert events[1][0] == 5

    @pytest.mark.asyncio
    async def test_trim_to_keep_last(self, store):
        # Store configured with keep_last=5
        for i in range(1, 11):
            await store.append("run-1", i, f'{{"seq":{i}}}')

        events = await store.replay("run-1")
        assert len(events) == 5
        assert events[0][0] == 6  # oldest kept
        assert events[4][0] == 10  # newest

    @pytest.mark.asyncio
    async def test_separate_runs(self, store):
        await store.append("run-a", 1, '{"run":"a"}')
        await store.append("run-b", 1, '{"run":"b"}')

        events_a = await store.replay("run-a")
        events_b = await store.replay("run-b")
        assert len(events_a) == 1
        assert len(events_b) == 1
        assert events_a[0][1] != events_b[0][1]

    @pytest.mark.asyncio
    async def test_replay_empty_run(self, store):
        events = await store.replay("nonexistent")
        assert events == []

    @pytest.mark.asyncio
    async def test_replay_after_seq_none(self, store):
        await store.append("run-1", 1, '{"a":1}')
        events = await store.replay("run-1", after_seq=None)
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_replay_after_seq_beyond_max(self, store):
        await store.append("run-1", 1, '{"a":1}')
        await store.append("run-1", 2, '{"a":2}')
        events = await store.replay("run-1", after_seq=99)
        assert events == []

    @pytest.mark.asyncio
    async def test_mark_terminal_first_time(self, store):
        result = await store.mark_terminal("run-1", "completed")
        assert result is True

    @pytest.mark.asyncio
    async def test_mark_terminal_idempotent(self, store):
        first = await store.mark_terminal("run-1", "completed")
        second = await store.mark_terminal("run-1", "failed")
        assert first is True
        assert second is False

    @pytest.mark.asyncio
    async def test_is_terminal(self, store):
        assert await store.is_terminal("run-1") is False
        await store.mark_terminal("run-1", "completed")
        assert await store.is_terminal("run-1") is True


# ---------------------------------------------------------------------------
# RedisReplayStore unit tests (mocked Redis dependency)
# ---------------------------------------------------------------------------


class TestRedisReplayStore:
    """Unit tests for RedisReplayStore with a mocked redis.asyncio.Redis client."""

    @pytest.fixture()
    def mock_redis(self):
        """Create a mock Redis client with all async methods.

        pipeline() is a regular method (not async) that returns a context-
        manager-like pipeline object whose chained methods return the
        pipeline itself, and execute() is async.
        """
        redis = AsyncMock()
        # pipeline() is sync -- returns a pipeline object, not a coroutine
        pipeline = MagicMock()
        pipeline.zadd = MagicMock(return_value=pipeline)
        pipeline.zremrangebyrank = MagicMock(return_value=pipeline)
        pipeline.expire = MagicMock(return_value=pipeline)
        pipeline.execute = AsyncMock(return_value=[1, 0, True, True])
        redis.pipeline = MagicMock(return_value=pipeline)
        return redis

    @pytest.fixture()
    def store(self, mock_redis):
        """Create a RedisReplayStore with injected mock Redis client.

        We bypass __init__ (which does a real redis import) and manually
        set the internal attributes to avoid needing redis installed.
        """
        config = ReplayConfig(keep_last=50, ttl_seconds=120, prefix="test")
        s = object.__new__(RedisReplayStore)
        s._redis = mock_redis
        s._config = config
        s._prefix = config.prefix
        return s

    def test_key_generation(self, store):
        """Verify key format: {prefix}:{run_id}:{suffix}."""
        assert store._events_key("abc-123") == "test:abc-123:events"
        assert store._seq_key("abc-123") == "test:abc-123:seq"
        assert store._terminal_key("abc-123") == "test:abc-123:terminal"

    def test_key_generation_special_chars(self, store):
        """Key format works with run IDs containing special characters."""
        assert store._events_key("run:with:colons") == "test:run:with:colons:events"
        assert store._seq_key("run-123_v2") == "test:run-123_v2:seq"

    async def test_next_seq(self, store, mock_redis):
        """next_seq() calls INCR and returns the integer result."""
        mock_redis.incr.return_value = 7

        result = await store.next_seq("run-1")

        assert result == 7
        mock_redis.incr.assert_awaited_once_with("test:run-1:seq")

    async def test_next_seq_returns_int(self, store, mock_redis):
        """next_seq() coerces the Redis response to int."""
        mock_redis.incr.return_value = "42"  # Redis may return string

        result = await store.next_seq("run-1")

        assert result == 42
        assert isinstance(result, int)

    async def test_append(self, store, mock_redis):
        """append() uses a pipeline with zadd, zremrangebyrank, and expire calls."""
        await store.append("run-1", 5, '{"type":"stage.started"}')

        pipeline = mock_redis.pipeline.return_value
        mock_redis.pipeline.assert_called_once_with(transaction=True)
        pipeline.zadd.assert_called_once_with(
            "test:run-1:events",
            {'5|{"type":"stage.started"}': 5.0},
        )
        pipeline.zremrangebyrank.assert_called_once_with(
            "test:run-1:events",
            0,
            -51,  # -(keep_last + 1)
        )
        # Two expire calls: events key and seq key
        assert pipeline.expire.call_count == 2
        expire_calls = pipeline.expire.call_args_list
        assert expire_calls[0].args == ("test:run-1:events", 120)
        assert expire_calls[1].args == ("test:run-1:seq", 120)
        pipeline.execute.assert_awaited_once()

    async def test_append_member_format(self, store, mock_redis):
        """Verify the ZSET member is formatted as '{seq}|{payload}'."""
        await store.append("run-x", 99, '{"data":"hello"}')

        pipeline = mock_redis.pipeline.return_value
        zadd_args = pipeline.zadd.call_args
        mapping = zadd_args.args[1]
        assert '99|{"data":"hello"}' in mapping
        assert mapping['99|{"data":"hello"}'] == 99.0

    async def test_replay_all(self, store, mock_redis):
        """replay() without after_seq calls zrange and parses members."""
        mock_redis.zrange.return_value = [
            ('1|{"type":"run.started"}', 1.0),
            ('2|{"type":"stage.started"}', 2.0),
            ('3|{"type":"stage.completed"}', 3.0),
        ]

        result = await store.replay("run-1")

        mock_redis.zrange.assert_awaited_once_with(
            "test:run-1:events", 0, -1, withscores=True
        )
        assert len(result) == 3
        assert result[0] == (1, '{"type":"run.started"}')
        assert result[1] == (2, '{"type":"stage.started"}')
        assert result[2] == (3, '{"type":"stage.completed"}')

    async def test_replay_all_empty(self, store, mock_redis):
        """replay() returns empty list when no events stored."""
        mock_redis.zrange.return_value = []

        result = await store.replay("nonexistent")

        assert result == []

    async def test_replay_after_seq(self, store, mock_redis):
        """replay() with after_seq calls zrangebyscore with exclusive min."""
        mock_redis.zrangebyscore.return_value = [
            ('4|{"seq":4}', 4.0),
            ('5|{"seq":5}', 5.0),
        ]

        result = await store.replay("run-1", after_seq=3)

        mock_redis.zrangebyscore.assert_awaited_once_with(
            "test:run-1:events", min="(3", max="+inf", withscores=True
        )
        assert len(result) == 2
        assert result[0] == (4, '{"seq":4}')
        assert result[1] == (5, '{"seq":5}')

    async def test_replay_after_seq_empty(self, store, mock_redis):
        """replay() with after_seq beyond max returns empty list."""
        mock_redis.zrangebyscore.return_value = []

        result = await store.replay("run-1", after_seq=999)

        assert result == []

    async def test_replay_member_without_pipe(self, store, mock_redis):
        """replay() handles malformed members without '|' separator."""
        mock_redis.zrange.return_value = [
            ("raw-payload-no-pipe", 1.0),
        ]

        result = await store.replay("run-1")

        # Fallback: returns the full member as payload
        assert result == [(1, "raw-payload-no-pipe")]

    async def test_replay_member_with_multiple_pipes(self, store, mock_redis):
        """replay() only splits on the first '|' to preserve payload content."""
        mock_redis.zrange.return_value = [
            ('10|{"data":"a|b|c"}', 10.0),
        ]

        result = await store.replay("run-1")

        assert result == [(10, '{"data":"a|b|c"}')]

    async def test_mark_terminal_first_time(self, store, mock_redis):
        """mark_terminal() returns True when SET NX succeeds (first call)."""
        mock_redis.set.return_value = True

        result = await store.mark_terminal("run-1", "completed")

        assert result is True
        mock_redis.set.assert_awaited_once_with(
            "test:run-1:terminal",
            "completed",
            nx=True,
            ex=120,
        )

    async def test_mark_terminal_duplicate(self, store, mock_redis):
        """mark_terminal() returns False when SET NX fails (already set)."""
        mock_redis.set.return_value = None  # Redis returns None when NX fails

        result = await store.mark_terminal("run-1", "failed")

        assert result is False

    async def test_mark_terminal_with_different_types(self, store, mock_redis):
        """mark_terminal() passes the terminal_type as the value."""
        mock_redis.set.return_value = True

        await store.mark_terminal("run-1", "cancelled")

        mock_redis.set.assert_awaited_once_with(
            "test:run-1:terminal",
            "cancelled",
            nx=True,
            ex=120,
        )

    async def test_is_terminal_true(self, store, mock_redis):
        """is_terminal() returns True when the terminal key exists."""
        mock_redis.exists.return_value = 1

        result = await store.is_terminal("run-1")

        assert result is True
        mock_redis.exists.assert_awaited_once_with("test:run-1:terminal")

    async def test_is_terminal_false(self, store, mock_redis):
        """is_terminal() returns False when the terminal key does not exist."""
        mock_redis.exists.return_value = 0

        result = await store.is_terminal("run-1")

        assert result is False

    async def test_close(self, store, mock_redis):
        """close() calls redis.close()."""
        await store.close()

        mock_redis.close.assert_awaited_once()

    def test_default_config(self, mock_redis):
        """RedisReplayStore uses default ReplayConfig when none provided."""
        s = object.__new__(RedisReplayStore)
        default_config = ReplayConfig()
        s._redis = mock_redis
        s._config = default_config
        s._prefix = default_config.prefix
        assert s._config.keep_last == 100
        assert s._config.ttl_seconds == 30 * 60
        assert s._prefix == "runs"

    def test_custom_prefix(self, mock_redis):
        """RedisReplayStore respects a custom prefix in ReplayConfig."""
        config = ReplayConfig(prefix="myapp")
        s = object.__new__(RedisReplayStore)
        s._redis = mock_redis
        s._config = config
        s._prefix = config.prefix
        assert s._events_key("r1") == "myapp:r1:events"

    def test_init_with_redis_mock(self):
        """RedisReplayStore.__init__ calls Redis.from_url with decode_responses."""
        import sys

        mock_redis_instance = AsyncMock()

        # Create a fake redis.asyncio module with a Redis class
        mock_redis_cls = MagicMock()
        mock_redis_cls.from_url.return_value = mock_redis_instance

        fake_redis_asyncio = MagicMock()
        fake_redis_asyncio.Redis = mock_redis_cls

        fake_redis = MagicMock()
        fake_redis.asyncio = fake_redis_asyncio

        # Inject into sys.modules so the local import resolves
        saved = {k: sys.modules.get(k) for k in ("redis", "redis.asyncio")}
        sys.modules["redis"] = fake_redis
        sys.modules["redis.asyncio"] = fake_redis_asyncio
        try:
            s = RedisReplayStore(
                redis_url="redis://myhost:6380/2",
                config=ReplayConfig(prefix="prod", keep_last=200),
            )
            mock_redis_cls.from_url.assert_called_once_with(
                "redis://myhost:6380/2", decode_responses=True
            )
            assert s._redis is mock_redis_instance
            assert s._config.keep_last == 200
            assert s._prefix == "prod"
        finally:
            # Restore original sys.modules state
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
