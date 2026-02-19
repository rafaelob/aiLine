"""Tests for Container lifecycle methods: health_check, close, validate, repr.

Covers the 64% uncovered lines in shared/container.py:
- health_check with DB pool stats and Redis connectivity
- health_check when pool raises an error
- close() disposing engines and event bus
- close() logging errors without raising
- validate() in production mode (ValueError)
- validate() with missing critical ports
- validate() with missing optional ports
- __repr__ display of adapters
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ailine_runtime.shared.config import LLMConfig, RedisConfig, Settings
from ailine_runtime.shared.container import Container, ValidationResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_container(**overrides: Any) -> Container:
    """Create a Container with test defaults."""
    settings = Settings(
        anthropic_api_key="",
        openai_api_key="",
        google_api_key="",
        openrouter_api_key="",
        llm=LLMConfig(provider="fake", api_key=""),
        redis=RedisConfig(url=""),
    )
    defaults: dict[str, Any] = {
        "settings": settings,
        "llm": MagicMock(),
        "event_bus": MagicMock(),
    }
    defaults.update(overrides)
    return Container(**defaults)


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_no_db_no_redis(self):
        """When no cleanup items and no Redis, returns unavailable for both."""
        container = _make_container(event_bus=None, _cleanup=[])
        result = await container.health_check()
        assert result["db"]["status"] == "unavailable"
        assert result["redis"]["status"] == "unavailable"

    @pytest.mark.asyncio
    async def test_db_pool_stats(self):
        """When engine with pool is in cleanup, reports pool stats."""
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool.checkedin.return_value = 8
        mock_pool.checkedout.return_value = 2
        mock_pool.overflow.return_value = 0

        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        container = _make_container(event_bus=None, _cleanup=[mock_engine])
        result = await container.health_check()
        assert result["db"]["status"] == "ok"
        assert result["db"]["pool_size"] == 10
        assert result["db"]["checked_in"] == 8
        assert result["db"]["checked_out"] == 2
        assert result["db"]["overflow"] == 0

    @pytest.mark.asyncio
    async def test_db_pool_error(self):
        """When pool stats raise, reports error status."""
        mock_pool = MagicMock()
        mock_pool.size.side_effect = RuntimeError("pool error")

        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        container = _make_container(event_bus=None, _cleanup=[mock_engine])
        result = await container.health_check()
        assert result["db"]["status"] == "error"
        assert "pool error" in result["db"]["detail"]

    @pytest.mark.asyncio
    async def test_redis_ping_ok(self):
        """When event bus ping succeeds, reports ok."""
        mock_event_bus = AsyncMock()
        mock_event_bus.ping.return_value = True

        container = _make_container(event_bus=mock_event_bus, _cleanup=[])
        result = await container.health_check()
        assert result["redis"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_redis_ping_error(self):
        """When event bus ping raises, reports error."""
        mock_event_bus = AsyncMock()
        mock_event_bus.ping.side_effect = ConnectionError("redis down")

        container = _make_container(event_bus=mock_event_bus, _cleanup=[])
        result = await container.health_check()
        assert result["redis"]["status"] == "error"
        assert "redis down" in result["redis"]["detail"]

    @pytest.mark.asyncio
    async def test_redis_ping_unreachable(self):
        """When event bus ping returns False, reports unreachable."""
        mock_event_bus = AsyncMock()
        mock_event_bus.ping.return_value = False

        container = _make_container(event_bus=mock_event_bus, _cleanup=[])
        result = await container.health_check()
        assert result["redis"]["status"] == "unreachable"


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------


class TestClose:
    @pytest.mark.asyncio
    async def test_disposes_engines(self):
        """close() should call dispose() on each cleanup item."""
        mock_engine = AsyncMock()
        container = _make_container(event_bus=None, _cleanup=[mock_engine])
        await container.close()
        mock_engine.dispose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_closes_event_bus(self):
        """close() should call close() on event_bus if available."""
        mock_bus = AsyncMock()
        mock_bus.close = AsyncMock()
        container = _make_container(event_bus=mock_bus, _cleanup=[])
        await container.close()
        mock_bus.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_engine_dispose_error_logged_not_raised(self):
        """close() should log but not raise on engine dispose failure."""
        mock_engine = AsyncMock()
        mock_engine.dispose.side_effect = RuntimeError("dispose error")
        container = _make_container(event_bus=None, _cleanup=[mock_engine])
        # Should not raise
        await container.close()

    @pytest.mark.asyncio
    async def test_event_bus_close_error_logged_not_raised(self):
        """close() should log but not raise on event bus close failure."""
        mock_bus = AsyncMock()
        mock_bus.close = AsyncMock(side_effect=RuntimeError("bus close error"))
        container = _make_container(event_bus=mock_bus, _cleanup=[])
        # Should not raise
        await container.close()

    @pytest.mark.asyncio
    async def test_close_multiple_engines(self):
        """close() should dispose all engines in _cleanup."""
        engines = [AsyncMock() for _ in range(3)]
        container = _make_container(event_bus=None, _cleanup=engines)
        await container.close()
        for eng in engines:
            eng.dispose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_no_event_bus(self):
        """close() should handle event_bus=None gracefully."""
        container = _make_container(event_bus=None, _cleanup=[])
        await container.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_close_event_bus_without_close_method(self):
        """close() should skip event_bus if it has no close method."""
        mock_bus = MagicMock(spec=[])  # No attributes at all
        container = _make_container(event_bus=mock_bus, _cleanup=[])
        await container.close()  # Should not raise


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


class TestValidate:
    def test_validate_all_present(self):
        """All required ports present should return ok=True."""
        container = _make_container()
        result = container.validate()
        assert isinstance(result, ValidationResult)
        assert result.ok is True
        assert result.missing_critical == []

    def test_validate_missing_llm(self):
        """Missing llm should report as critical."""
        container = _make_container(llm=None)
        result = container.validate()
        assert result.ok is False
        assert "llm" in result.missing_critical

    def test_validate_missing_event_bus(self):
        """Missing event_bus should report as critical."""
        container = _make_container(event_bus=None)
        result = container.validate()
        assert result.ok is False
        assert "event_bus" in result.missing_critical

    def test_validate_missing_both_critical(self):
        container = _make_container(llm=None, event_bus=None)
        result = container.validate()
        assert result.ok is False
        assert "llm" in result.missing_critical
        assert "event_bus" in result.missing_critical

    def test_validate_production_raises_on_missing_critical(self):
        """Production mode should raise ValueError on missing critical ports."""
        settings = Settings(
            anthropic_api_key="",
            openai_api_key="",
            google_api_key="",
            openrouter_api_key="",
            env="production",
            llm=LLMConfig(provider="fake", api_key=""),
            redis=RedisConfig(url=""),
        )
        container = Container(settings=settings, llm=None, event_bus=MagicMock())
        with pytest.raises(ValueError, match="production"):
            container.validate()

    def test_validate_missing_optional_reported(self):
        """Missing optional ports should be reported but ok remains True."""
        container = _make_container(
            vectorstore=None,
            embeddings=None,
            stt=None,
            tts=None,
            image_describer=None,
            ocr=None,
            sign_recognition=None,
        )
        result = container.validate()
        assert result.ok is True
        assert "vectorstore" in result.missing_optional
        assert "embeddings" in result.missing_optional
        assert "stt" in result.missing_optional
        assert "tts" in result.missing_optional
        assert "image_describer" in result.missing_optional
        assert "ocr" in result.missing_optional
        assert "sign_recognition" in result.missing_optional

    def test_validate_optional_present_not_reported(self):
        """Present optional ports should not appear in missing_optional."""
        container = _make_container(
            vectorstore=MagicMock(),
            embeddings=MagicMock(),
        )
        result = container.validate()
        assert "vectorstore" not in result.missing_optional
        assert "embeddings" not in result.missing_optional


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


class TestRepr:
    def test_repr_shows_adapter_types(self):
        container = _make_container()
        r = repr(container)
        assert "Container(" in r
        assert "llm=MagicMock" in r or "llm=" in r
        assert "event_bus=" in r

    def test_repr_shows_none_for_missing(self):
        container = _make_container(
            vectorstore=None,
            embeddings=None,
            stt=None,
            tts=None,
            image_describer=None,
            ocr=None,
            sign_recognition=None,
        )
        r = repr(container)
        assert "vectorstore=None" in r
        assert "embeddings=None" in r

    def test_repr_includes_env(self):
        container = _make_container()
        r = repr(container)
        assert "env=" in r
