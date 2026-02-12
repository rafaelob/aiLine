"""Tests for ElevenLabsTTS adapter -- covers all 20 lines (0% -> ~100%).

Tests the synthesize method with mocked httpx.AsyncClient.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ailine_runtime.adapters.media.elevenlabs_tts import ElevenLabsTTS

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tts() -> ElevenLabsTTS:
    return ElevenLabsTTS(api_key="test-key", voice_id="voice-123", model_id="eleven_multilingual_v2")


# ===========================================================================
# Constructor tests
# ===========================================================================


class TestElevenLabsTTSInit:
    def test_default_values(self):
        tts = ElevenLabsTTS()
        assert tts._api_key == ""
        assert tts._voice_id == "default"
        assert tts._model_id == "eleven_multilingual_v2"

    def test_custom_values(self):
        tts = ElevenLabsTTS(api_key="k", voice_id="v", model_id="m")
        assert tts._api_key == "k"
        assert tts._voice_id == "v"
        assert tts._model_id == "m"


# ===========================================================================
# synthesize tests
# ===========================================================================


class TestSynthesize:
    async def test_synthesize_returns_bytes(self, tts: ElevenLabsTTS):
        """synthesize should return the response content bytes."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"\xff\xd8audio-data-here"
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client_instance):
            result = await tts.synthesize("Hello world")

        assert result == b"\xff\xd8audio-data-here"

    async def test_synthesize_sends_correct_url(self, tts: ElevenLabsTTS):
        """The URL should include the voice_id."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await tts.synthesize("test")

        call_args = mock_client.post.call_args
        url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url", "")
        assert "voice-123" in url
        assert "text-to-speech" in url

    async def test_synthesize_sends_correct_headers(self, tts: ElevenLabsTTS):
        """Headers should include xi-api-key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await tts.synthesize("test")

        call_kwargs = mock_client.post.call_args.kwargs
        headers = call_kwargs.get("headers", {})
        assert headers["xi-api-key"] == "test-key"

    async def test_synthesize_sends_correct_payload(self, tts: ElevenLabsTTS):
        """Payload should contain text, model_id, and voice_settings."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await tts.synthesize("Ola mundo", locale="pt-BR", speed=1.5)

        call_kwargs = mock_client.post.call_args.kwargs
        payload = call_kwargs.get("json", {})
        assert payload["text"] == "Ola mundo"
        assert payload["model_id"] == "eleven_multilingual_v2"
        assert "voice_settings" in payload
        assert payload["voice_settings"]["stability"] == 0.5
        assert payload["voice_settings"]["similarity_boost"] == 0.75

    async def test_synthesize_raises_on_http_error(self, tts: ElevenLabsTTS):
        """When the API returns an error, raise_for_status should propagate it."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 401

        def raise_error():
            raise httpx.HTTPStatusError(
                "Unauthorized",
                request=MagicMock(),
                response=mock_response,
            )

        mock_response.raise_for_status = raise_error
        mock_response.content = b""

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("httpx.AsyncClient", return_value=mock_client),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await tts.synthesize("test")
