"""Tests for OpenAI STT adapter -- mocks the OpenAI SDK."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_openai():
    """Mock the openai module."""
    mock_module = MagicMock()
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.text = "Transcribed text"
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)
    mock_module.AsyncOpenAI.return_value = mock_client
    return mock_module, mock_client, mock_response


class TestOpenAISTTInit:
    def test_default_params(self, mock_openai):
        mock_module, _, _ = mock_openai
        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.media.openai_stt import OpenAISTT

            stt = OpenAISTT()
            assert stt._model == "gpt-4o-transcribe"
            assert stt._client is None

    def test_custom_params(self, mock_openai):
        mock_module, _, _ = mock_openai
        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.media.openai_stt import OpenAISTT

            stt = OpenAISTT(api_key="sk-test", model="gpt-4o-mini-transcribe")
            assert stt._model == "gpt-4o-mini-transcribe"
            assert stt._api_key == "sk-test"


class TestOpenAISTTEnsureClient:
    def test_lazy_init_with_key(self, mock_openai):
        mock_module, _, _ = mock_openai
        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.media.openai_stt import OpenAISTT

            stt = OpenAISTT(api_key="sk-test")
            assert stt._client is None
            stt._ensure_client()
            assert stt._client is not None
            mock_module.AsyncOpenAI.assert_called_once_with(api_key="sk-test")

    def test_lazy_init_without_key(self, mock_openai):
        mock_module, _, _ = mock_openai
        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.media.openai_stt import OpenAISTT

            stt = OpenAISTT()
            stt._ensure_client()
            mock_module.AsyncOpenAI.assert_called_once_with()

    def test_client_loaded_only_once(self, mock_openai):
        mock_module, _, _ = mock_openai
        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.media.openai_stt import OpenAISTT

            stt = OpenAISTT()
            stt._ensure_client()
            stt._ensure_client()
            mock_module.AsyncOpenAI.assert_called_once()

    def test_import_error(self):
        with patch.dict("sys.modules", {"openai": None}):
            from ailine_runtime.adapters.media.openai_stt import OpenAISTT

            stt = OpenAISTT()
            with pytest.raises(ImportError, match="openai"):
                stt._ensure_client()


class TestOpenAISTTTranscribe:
    @pytest.mark.asyncio
    async def test_transcribe(self, mock_openai):
        mock_module, mock_client, _ = mock_openai
        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.media.openai_stt import OpenAISTT

            stt = OpenAISTT(api_key="sk-test")
            result = await stt.transcribe(b"audio bytes", language="pt")
            assert result == "Transcribed text"
            mock_client.audio.transcriptions.create.assert_called_once()
            call_kwargs = mock_client.audio.transcriptions.create.call_args
            assert call_kwargs.kwargs["model"] == "gpt-4o-transcribe"
            assert call_kwargs.kwargs["language"] == "pt"

    @pytest.mark.asyncio
    async def test_transcribe_english(self, mock_openai):
        mock_module, mock_client, _ = mock_openai
        with patch.dict("sys.modules", {"openai": mock_module}):
            from ailine_runtime.adapters.media.openai_stt import OpenAISTT

            stt = OpenAISTT(api_key="sk-test")
            await stt.transcribe(b"audio", language="en")
            call_kwargs = mock_client.audio.transcriptions.create.call_args
            assert call_kwargs.kwargs["language"] == "en"
