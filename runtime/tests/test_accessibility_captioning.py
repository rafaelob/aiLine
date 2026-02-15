"""Tests for Libras captioning backend: GlossToTextTranslator, CaptionOrchestrator, and WebSocket.

Covers:
- GlossToTextTranslator: translation, caching, empty input
- CaptionOrchestrator: partial/final message handling, debouncing, rate limiting
- WebSocket endpoint: protocol messages, error handling
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from ailine_runtime.accessibility.caption_orchestrator import (
    MSG_CAPTION_DRAFT,
    MSG_CAPTION_FINAL,
    CaptionOrchestrator,
)
from ailine_runtime.accessibility.gloss_translator import GlossToTextTranslator
from ailine_runtime.domain.ports.llm import WebSearchResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class FakeLLMForTranslation:
    """Minimal fake LLM that returns gloss input back as 'translated' text."""

    model_name = "fake-translator"

    @property
    def capabilities(self) -> dict[str, Any]:
        return {"provider": "fake", "streaming": True}

    async def generate(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        user_msg = messages[-1]["content"]
        return f"Traduzido: {user_msg}"

    def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 1.0,
        max_tokens: int = 4096,
        **kwargs: Any,
    ):  # type: ignore[return]
        user_msg = messages[-1]["content"]
        result = f"Traduzido: {user_msg}"

        async def _gen():  # type: ignore[return]
            for char in result:
                yield char

        return _gen()

    async def generate_with_search(
        self,
        query: str,
        *,
        max_results: int = 5,
        **kwargs: Any,
    ) -> WebSearchResult:
        return WebSearchResult(text=f"Search result for: {query}")


@pytest.fixture
def fake_llm() -> FakeLLMForTranslation:
    return FakeLLMForTranslation()


@pytest.fixture
def translator(fake_llm: FakeLLMForTranslation) -> GlossToTextTranslator:
    return GlossToTextTranslator(llm=fake_llm)


@pytest.fixture
def emitted_messages() -> list[dict[str, Any]]:
    return []


@pytest.fixture
def orchestrator(
    translator: GlossToTextTranslator,
    emitted_messages: list[dict[str, Any]],
) -> CaptionOrchestrator:
    async def emit(msg: dict[str, Any]) -> None:
        emitted_messages.append(msg)

    return CaptionOrchestrator(
        translator=translator,
        emit=emit,
        max_hz=100.0,  # high rate for fast tests
        debounce_ms=50,  # short debounce for tests
        commit_threshold=0.80,
    )


# ===========================================================================
# GlossToTextTranslator
# ===========================================================================


class TestGlossToTextTranslator:
    """Tests for gloss-to-text translation."""

    async def test_translate_empty_glosses(self, translator: GlossToTextTranslator):
        result = await translator.translate([])
        assert result == ""

    async def test_translate_single_gloss(self, translator: GlossToTextTranslator):
        result = await translator.translate(["OI"])
        assert "OI" in result

    async def test_translate_multiple_glosses(self, translator: GlossToTextTranslator):
        result = await translator.translate(["EU", "GOSTAR", "ESCOLA"])
        assert "EU GOSTAR ESCOLA" in result

    async def test_cache_hit(self, translator: GlossToTextTranslator):
        r1 = await translator.translate(["OI"])
        r2 = await translator.translate(["OI"])
        assert r1 == r2

    async def test_cache_different_input(self, translator: GlossToTextTranslator):
        r1 = await translator.translate(["OI"])
        r2 = await translator.translate(["SIM"])
        assert r1 != r2

    async def test_cache_eviction(self):
        llm = FakeLLMForTranslation()
        translator = GlossToTextTranslator(llm=llm, cache_size=2)
        await translator.translate(["A"])
        await translator.translate(["B"])
        await translator.translate(["C"])  # should evict "A"
        # No assertion on cache internals; just verify no errors

    async def test_clear_cache(self, translator: GlossToTextTranslator):
        await translator.translate(["OI"])
        translator.clear_cache()
        # Second call should not be cached (no way to tell externally,
        # but verifies no crash)
        r2 = await translator.translate(["OI"])
        assert "OI" in r2

    async def test_streaming_translation(self, translator: GlossToTextTranslator):
        chunks: list[str] = []
        async for chunk in translator.translate_streaming(["EU", "GOSTAR"]):
            chunks.append(chunk)
        full = "".join(chunks)
        assert "EU GOSTAR" in full

    async def test_streaming_empty_glosses(self, translator: GlossToTextTranslator):
        chunks: list[str] = []
        async for chunk in translator.translate_streaming([]):
            chunks.append(chunk)
        assert chunks == []

    async def test_streaming_cache_hit(self, translator: GlossToTextTranslator):
        # Pre-populate cache
        await translator.translate(["OI"])
        # Streaming should use cache
        chunks: list[str] = []
        async for chunk in translator.translate_streaming(["OI"]):
            chunks.append(chunk)
        assert len(chunks) == 1  # Single chunk from cache


# ===========================================================================
# CaptionOrchestrator
# ===========================================================================


class TestCaptionOrchestrator:
    """Tests for caption orchestration."""

    async def test_handle_final_message(
        self,
        orchestrator: CaptionOrchestrator,
        emitted_messages: list[dict[str, Any]],
    ):
        await orchestrator.handle_message(
            {
                "type": "gloss_final",
                "glosses": ["OI", "TUDO-BEM"],
                "confidence": 0.95,
                "ts": 1234,
            }
        )
        # Should emit a caption_final_delta
        assert len(emitted_messages) >= 1
        final_msgs = [m for m in emitted_messages if m["type"] == MSG_CAPTION_FINAL]
        assert len(final_msgs) == 1
        assert "text" in final_msgs[0]
        assert final_msgs[0]["glosses"] == ["OI", "TUDO-BEM"]

    async def test_handle_partial_debounced(
        self,
        orchestrator: CaptionOrchestrator,
        emitted_messages: list[dict[str, Any]],
    ):
        await orchestrator.handle_message(
            {
                "type": "gloss_partial",
                "glosses": ["EU"],
                "confidence": 0.50,
            }
        )
        # Wait for debounce
        await asyncio.sleep(0.15)
        draft_msgs = [m for m in emitted_messages if m["type"] == MSG_CAPTION_DRAFT]
        assert len(draft_msgs) >= 1

    async def test_partial_auto_commit_on_high_confidence(
        self,
        orchestrator: CaptionOrchestrator,
        emitted_messages: list[dict[str, Any]],
    ):
        await orchestrator.handle_message(
            {
                "type": "gloss_partial",
                "glosses": ["OBRIGADO"],
                "confidence": 0.95,  # above commit_threshold
            }
        )
        # Wait a bit for async processing
        await asyncio.sleep(0.1)
        final_msgs = [m for m in emitted_messages if m["type"] == MSG_CAPTION_FINAL]
        assert len(final_msgs) >= 1

    async def test_unknown_message_type(
        self,
        orchestrator: CaptionOrchestrator,
        emitted_messages: list[dict[str, Any]],
    ):
        # Should not crash on unknown types
        await orchestrator.handle_message({"type": "unknown_type"})
        await asyncio.sleep(0.05)
        # No messages emitted for unknown type
        assert len(emitted_messages) == 0

    async def test_reset_clears_state(
        self,
        orchestrator: CaptionOrchestrator,
        emitted_messages: list[dict[str, Any]],
    ):
        await orchestrator.handle_message(
            {
                "type": "gloss_final",
                "glosses": ["OI"],
                "confidence": 0.90,
            }
        )
        orchestrator.reset()
        # After reset, new final message should start fresh
        emitted_messages.clear()
        await orchestrator.handle_message(
            {
                "type": "gloss_final",
                "glosses": ["SIM"],
                "confidence": 0.90,
            }
        )
        final_msgs = [m for m in emitted_messages if m["type"] == MSG_CAPTION_FINAL]
        assert len(final_msgs) == 1
        # full_text should be just the new translation (not cumulative)
        assert "full_text" in final_msgs[0]

    async def test_empty_glosses_final(
        self,
        orchestrator: CaptionOrchestrator,
        emitted_messages: list[dict[str, Any]],
    ):
        await orchestrator.handle_message(
            {
                "type": "gloss_final",
                "glosses": [],
                "confidence": 0.0,
            }
        )
        # No final messages for empty glosses
        final_msgs = [m for m in emitted_messages if m["type"] == MSG_CAPTION_FINAL]
        assert len(final_msgs) == 0


# ===========================================================================
# WebSocket Endpoint (integration via test client)
# ===========================================================================


class TestLibrasCaptionWebSocket:
    """Test the WebSocket endpoint for Libras captioning."""

    @pytest.fixture
    def client(self, monkeypatch):
        monkeypatch.setenv("AILINE_DEV_MODE", "true")

        from starlette.testclient import TestClient

        from ailine_runtime.api.app import create_app
        from ailine_runtime.shared.config import Settings

        settings = Settings()
        application = create_app(settings)
        return TestClient(application)

    def test_websocket_accepts_connection(self, client):
        """Verify the WS endpoint accepts connections and responds to messages."""
        with client.websocket_connect("/sign-language/ws/libras-caption") as ws:
            # Send an invalid type to get an immediate error response
            # (gloss_final triggers async LLM + rate-limiter sleeps that
            # deadlock Starlette's sync TestClient, so we test the full
            # pipeline via CaptionOrchestrator unit tests above instead)
            ws.send_text(json.dumps({"type": "probe"}))
            response = json.loads(ws.receive_text())
            assert response["type"] == "error"

    def test_websocket_invalid_json(self, client):
        with client.websocket_connect("/sign-language/ws/libras-caption") as ws:
            ws.send_text("not valid json")
            response = json.loads(ws.receive_text())
            assert response["type"] == "error"
            assert "Invalid JSON" in response["detail"]

    def test_websocket_unknown_message_type(self, client):
        with client.websocket_connect("/sign-language/ws/libras-caption") as ws:
            ws.send_text(json.dumps({"type": "bad_type"}))
            response = json.loads(ws.receive_text())
            assert response["type"] == "error"
            assert "Unknown message type" in response["detail"]
