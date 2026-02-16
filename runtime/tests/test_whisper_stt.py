"""Tests for WhisperSTT adapter -- mocks faster-whisper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_faster_whisper():
    """Mock the faster_whisper module."""
    mock_module = MagicMock()
    mock_model = MagicMock()

    seg1 = MagicMock()
    seg1.text = "Ola"
    seg2 = MagicMock()
    seg2.text = "mundo"
    mock_model.transcribe.return_value = ([seg1, seg2], MagicMock())

    mock_module.WhisperModel.return_value = mock_model
    return mock_module, mock_model


class TestWhisperSTTInit:
    def test_default_params(self, mock_faster_whisper):
        mock_module, _ = mock_faster_whisper
        with patch.dict("sys.modules", {"faster_whisper": mock_module}):
            from ailine_runtime.adapters.media.whisper_stt import WhisperSTT

            stt = WhisperSTT()
            assert stt._model_size == "turbo"
            assert stt._device == "cpu"
            assert stt._compute_type == "int8"
            assert stt._model is None

    def test_custom_params(self, mock_faster_whisper):
        mock_module, _ = mock_faster_whisper
        with patch.dict("sys.modules", {"faster_whisper": mock_module}):
            from ailine_runtime.adapters.media.whisper_stt import WhisperSTT

            stt = WhisperSTT(
                model_size="large-v3", device="cuda", compute_type="float16"
            )
            assert stt._model_size == "large-v3"
            assert stt._device == "cuda"


class TestWhisperSTTEnsureModel:
    def test_lazy_load(self, mock_faster_whisper):
        mock_module, _ = mock_faster_whisper
        with patch.dict("sys.modules", {"faster_whisper": mock_module}):
            from ailine_runtime.adapters.media.whisper_stt import WhisperSTT

            stt = WhisperSTT()
            assert stt._model is None
            stt._ensure_model()
            assert stt._model is not None
            mock_module.WhisperModel.assert_called_once_with(
                "turbo", device="cpu", compute_type="int8"
            )

    def test_model_loaded_only_once(self, mock_faster_whisper):
        mock_module, _ = mock_faster_whisper
        with patch.dict("sys.modules", {"faster_whisper": mock_module}):
            from ailine_runtime.adapters.media.whisper_stt import WhisperSTT

            stt = WhisperSTT()
            stt._ensure_model()
            stt._ensure_model()
            mock_module.WhisperModel.assert_called_once()

    def test_import_error(self):
        with patch.dict("sys.modules", {"faster_whisper": None}):
            from ailine_runtime.adapters.media.whisper_stt import WhisperSTT

            stt = WhisperSTT()
            with pytest.raises(ImportError, match="faster-whisper"):
                stt._ensure_model()


class TestWhisperSTTTranscribe:
    @pytest.mark.asyncio
    async def test_transcribe(self, mock_faster_whisper):
        mock_module, _mock_model = mock_faster_whisper
        with patch.dict("sys.modules", {"faster_whisper": mock_module}):
            from ailine_runtime.adapters.media.whisper_stt import WhisperSTT

            stt = WhisperSTT()
            result = await stt.transcribe(b"fake audio bytes", language="pt")
            assert result == "Ola mundo"

    @pytest.mark.asyncio
    async def test_transcribe_empty_segments(self, mock_faster_whisper):
        mock_module, mock_model = mock_faster_whisper
        mock_model.transcribe.return_value = ([], MagicMock())
        with patch.dict("sys.modules", {"faster_whisper": mock_module}):
            from ailine_runtime.adapters.media.whisper_stt import WhisperSTT

            stt = WhisperSTT()
            result = await stt.transcribe(b"audio", language="en")
            assert result == ""


class TestSyncTranscribe:
    def test_temp_file_cleanup(self, mock_faster_whisper):
        """Verify temp file is created and cleaned up."""
        mock_module, mock_model = mock_faster_whisper
        with patch.dict("sys.modules", {"faster_whisper": mock_module}):
            from ailine_runtime.adapters.media.whisper_stt import WhisperSTT

            stt = WhisperSTT()
            stt._ensure_model()
            result = stt._sync_transcribe(b"audio bytes", "pt")
            assert result == "Ola mundo"
            # Verify transcribe was called with a file path
            mock_model.transcribe.assert_called_once()
            call_args = mock_model.transcribe.call_args
            assert call_args[0][0].endswith(".wav")
