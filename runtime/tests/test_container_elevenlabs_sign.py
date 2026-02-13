"""Tests for container.py -- covers ElevenLabs TTS branch (lines 149-151) and
sign recognition MediaPipe branch (lines 173-178).

Line 149: from ..adapters.media.elevenlabs_tts import ElevenLabsTTS
Line 150-151: tts = ElevenLabsTTS(api_key=elevenlabs_key)
Lines 173-178: MediaPipe sign recognition branch with successful import
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from ailine_runtime.shared.config import Settings
from ailine_runtime.shared.container_adapters import build_media, build_sign_recognition

# ---------------------------------------------------------------------------
# Env-var isolation
# ---------------------------------------------------------------------------

_API_KEY_ENV_VARS = [
    "ANTHROPIC_API_KEY",
    "AILINE_ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "AILINE_OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "AILINE_GOOGLE_API_KEY",
    "OPENROUTER_API_KEY",
    "AILINE_OPENROUTER_API_KEY",
]


@pytest.fixture(autouse=True)
def _clean_api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _API_KEY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


# ===========================================================================
# ElevenLabs TTS branch (lines 149-151)
# ===========================================================================


class TestBuildMediaElevenLabsTTS:
    def test_elevenlabs_tts_when_key_available(self):
        """When elevenlabs_api_key is set, build ElevenLabsTTS (lines 149-151).

        The Settings class does not have an elevenlabs_api_key field;
        the container checks it via getattr(settings, "elevenlabs_api_key", "").
        We inject the attribute dynamically to simulate a config that has it.
        """
        settings = Settings()
        # Dynamically set the attribute the container reads via getattr
        object.__setattr__(settings, "elevenlabs_api_key", "el-test-key")

        _stt, tts, _describer, _ocr = build_media(settings)

        assert type(tts).__name__ == "ElevenLabsTTS"
        assert tts._api_key == "el-test-key"

    def test_fake_tts_when_no_elevenlabs_key(self):
        """Without elevenlabs_api_key, fall back to FakeTTS."""
        settings = Settings()
        _stt, tts, _describer, _ocr = build_media(settings)
        assert type(tts).__name__ == "FakeTTS"


# ===========================================================================
# Sign recognition MediaPipe branch (lines 173-178)
# ===========================================================================


class TestBuildSignRecognitionMediaPipe:
    def test_mediapipe_sign_recognition_when_available(self):
        """When model_path is set and mediapipe is importable, use MediaPipeSignRecognition.

        Lines 173-176: successful import and instantiation.
        The Settings class does not have sign_model_path; container reads via getattr.
        """
        mock_sign_rec_cls = MagicMock(name="MediaPipeSignRecognition")
        mock_sign_rec_instance = MagicMock(name="MediaPipeSignRecognition_instance")
        mock_sign_rec_cls.return_value = mock_sign_rec_instance

        # Create a mock module for sign_recognition
        mock_sign_module = MagicMock()
        mock_sign_module.MediaPipeSignRecognition = mock_sign_rec_cls

        sign_mod_key = "ailine_runtime.adapters.media.sign_recognition"
        saved = sys.modules.get(sign_mod_key)

        try:
            sys.modules[sign_mod_key] = mock_sign_module

            settings = Settings()
            object.__setattr__(settings, "sign_model_path", "/models/sign.tflite")
            sr = build_sign_recognition(settings)

            assert sr is mock_sign_rec_instance
            mock_sign_rec_cls.assert_called_once_with(model_path="/models/sign.tflite")
        finally:
            if saved is not None:
                sys.modules[sign_mod_key] = saved
            else:
                sys.modules.pop(sign_mod_key, None)

    def test_mediapipe_import_error_falls_back(self):
        """When model_path is set but import fails, fall back to FakeSignRecognition.

        Lines 177-178: ImportError caught, falls through to FakeSignRecognition.
        """
        sign_mod_key = "ailine_runtime.adapters.media.sign_recognition"
        saved = sys.modules.get(sign_mod_key)

        try:
            # Block the import
            sys.modules[sign_mod_key] = None  # type: ignore[assignment]

            settings = Settings()
            object.__setattr__(settings, "sign_model_path", "/models/sign.tflite")
            sr = build_sign_recognition(settings)

            assert type(sr).__name__ == "FakeSignRecognition"
        finally:
            if saved is not None:
                sys.modules[sign_mod_key] = saved
            else:
                sys.modules.pop(sign_mod_key, None)

    def test_no_model_path_uses_fake(self):
        """Without sign_model_path, always use FakeSignRecognition."""
        settings = Settings()
        sr = build_sign_recognition(settings)
        assert type(sr).__name__ == "FakeSignRecognition"
