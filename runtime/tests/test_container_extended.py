"""Extended tests for shared.container -- covers all builder branches."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from ailine_runtime.shared.config import EmbeddingConfig, LLMConfig, Settings
from ailine_runtime.shared.container_adapters import (
    build_embeddings as _build_embeddings,
)
from ailine_runtime.shared.container_adapters import (
    build_llm as _build_llm,
)
from ailine_runtime.shared.container_adapters import (
    build_media as _build_media,
)
from ailine_runtime.shared.container_adapters import (
    build_sign_recognition as _build_sign_recognition,
)
from ailine_runtime.shared.container_adapters import (
    resolve_api_key as _resolve_api_key,
)

# ---------------------------------------------------------------------------
# Pre-import adapters that depend on optional packages.
#
# openai_embeddings and openai_llm need the ``openai`` package at import
# time.  Since ``openai`` is not installed in the test environment, we
# temporarily inject a mock into sys.modules so that Python can execute
# the module files and cache them.  After this, every subsequent
# ``from ...openai_embeddings import OpenAIEmbeddings`` (e.g. inside
# _build_embeddings) simply finds the cached module -- no risk of
# triggering a numpy DLL reimport crash on Windows.
# ---------------------------------------------------------------------------
if "ailine_runtime.adapters.embeddings.openai_embeddings" not in sys.modules:
    _mock_openai = MagicMock()
    sys.modules.setdefault("openai", _mock_openai)
    try:
        import ailine_runtime.adapters.embeddings.openai_embeddings  # noqa: F401
    except Exception:
        pass
    finally:
        # Only remove the openai mock if we were the ones who inserted it
        if sys.modules.get("openai") is _mock_openai:
            del sys.modules["openai"]
    del _mock_openai

# ---------------------------------------------------------------------------
# Env-var isolation: ensure no real API keys leak into tests
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
    """Remove all API-key env vars so that Settings defaults to empty strings."""
    for var in _API_KEY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings_with_env_keys(
    monkeypatch: pytest.MonkeyPatch,
    *,
    anthropic: str = "",
    openai: str = "",
    google: str = "",
    openrouter: str = "",
    **kwargs,
) -> Settings:
    """Build Settings with API keys injected via env vars.

    The Settings class uses ``validation_alias=AliasChoices(...)`` so
    keyword arguments with the Python field name (e.g. ``anthropic_api_key``)
    are silently ignored (``extra="ignore"``).  We must set the env vars
    instead.
    """
    if anthropic:
        monkeypatch.setenv("ANTHROPIC_API_KEY", anthropic)
    if openai:
        monkeypatch.setenv("OPENAI_API_KEY", openai)
    if google:
        monkeypatch.setenv("GOOGLE_API_KEY", google)
    if openrouter:
        monkeypatch.setenv("OPENROUTER_API_KEY", openrouter)
    return Settings(**kwargs)


# ===========================================================================
# TestBuildLLM
# ===========================================================================


class TestBuildLLM:
    def test_anthropic_provider(self, monkeypatch: pytest.MonkeyPatch):
        settings = _settings_with_env_keys(
            monkeypatch,
            anthropic="sk-ant-test",
            llm={"provider": "anthropic", "api_key": "sk-ant-test"},
        )
        llm = _build_llm(settings)
        from ailine_runtime.adapters.llm.anthropic_llm import AnthropicChatLLM

        assert isinstance(llm, AnthropicChatLLM)

    def test_openai_provider(self, monkeypatch: pytest.MonkeyPatch):
        """openai package is not installed; mock it in sys.modules."""
        mock_openai = MagicMock()
        settings = _settings_with_env_keys(
            monkeypatch,
            openai="sk-oai-test",
            llm={"provider": "openai", "api_key": "sk-oai-test"},
        )
        with patch.dict(sys.modules, {"openai": mock_openai}):
            llm = _build_llm(settings)

        assert type(llm).__name__ == "OpenAIChatLLM"

    def test_openrouter_provider(self, monkeypatch: pytest.MonkeyPatch):
        """openai package is not installed; mock it in sys.modules."""
        mock_openai = MagicMock()
        settings = _settings_with_env_keys(
            monkeypatch,
            openrouter="sk-or-test",
            llm={"provider": "openrouter", "api_key": "sk-or-test"},
        )
        with patch.dict(sys.modules, {"openai": mock_openai}):
            llm = _build_llm(settings)

        assert type(llm).__name__ == "OpenAIChatLLM"

    def test_gemini_provider(self, monkeypatch: pytest.MonkeyPatch):
        """google-genai is not installed; mock the google.genai module."""
        mock_google = MagicMock()
        mock_genai = MagicMock()
        settings = _settings_with_env_keys(
            monkeypatch,
            google="gk-test",
            llm={"provider": "gemini", "api_key": "gk-test"},
        )
        with patch.dict(
            sys.modules,
            {"google": mock_google, "google.genai": mock_genai},
        ):
            llm = _build_llm(settings)
            # isinstance check INSIDE the with block to avoid class identity
            # issues caused by module reloading after patch exits.
            assert type(llm).__name__ == "GeminiChatLLM"

    def test_fake_provider(self):
        settings = Settings(llm=LLMConfig(provider="fake", api_key=""))
        llm = _build_llm(settings)
        from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM

        assert isinstance(llm, FakeChatLLM)

    def test_no_key_falls_back_to_fake(self):
        """When provider is valid but no API key is present, ADR-051 FakeLLM fallback."""
        settings = Settings(llm=LLMConfig(provider="anthropic", api_key=""))
        llm = _build_llm(settings)
        from ailine_runtime.adapters.llm.fake_llm import FakeChatLLM

        assert isinstance(llm, FakeChatLLM)


# ===========================================================================
# TestBuildEmbeddings
# ===========================================================================


class TestBuildEmbeddings:
    def test_no_api_key(self):
        settings = Settings(
            embedding=EmbeddingConfig(provider="gemini", api_key=""),
        )
        emb = _build_embeddings(settings)
        assert emb is None

    def test_gemini_embeddings(self):
        """google-genai not installed; mock it and check type name."""
        mock_google = MagicMock()
        mock_genai = MagicMock()
        settings = Settings(
            embedding=EmbeddingConfig(
                provider="gemini", api_key="gk-test", dimensions=1536
            ),
        )
        with patch.dict(
            sys.modules,
            {"google": mock_google, "google.genai": mock_genai},
        ):
            emb = _build_embeddings(settings)
            assert type(emb).__name__ == "GeminiEmbeddings"

    def test_openai_embeddings(self):
        """openai package not installed; mock it and check type name."""
        mock_openai = MagicMock()
        settings = Settings(
            embedding=EmbeddingConfig(
                provider="openai", api_key="sk-oai-test", dimensions=1536
            ),
        )
        with patch.dict(sys.modules, {"openai": mock_openai}):
            emb = _build_embeddings(settings)
            assert type(emb).__name__ == "OpenAIEmbeddings"

    def test_unsupported_provider_returns_none(self):
        """Provider='local' with a key still returns None (no adapter exists)."""
        settings = Settings(
            embedding=EmbeddingConfig(provider="local", api_key="some-key"),
        )
        emb = _build_embeddings(settings)
        assert emb is None


# ===========================================================================
# TestBuildMedia
# ===========================================================================


class TestBuildMedia:
    def test_openai_stt_when_key_available(self, monkeypatch: pytest.MonkeyPatch):
        settings = _settings_with_env_keys(
            monkeypatch,
            openai="sk-oai-test",
        )
        stt, _tts, _describer, _ocr = _build_media(settings)
        from ailine_runtime.adapters.media.openai_stt import OpenAISTT

        assert isinstance(stt, OpenAISTT)

    def test_fake_stt_when_no_key_and_no_whisper(self):
        """No OpenAI key + WhisperSTT import fails -> FakeSTT.

        The container does a lazy import:
            from ..adapters.media.whisper_stt import WhisperSTT
        Since the module is already cached (WhisperSTT does not import
        faster_whisper at module level), we set the sys.modules entry to
        None to make the import raise ImportError.
        """
        settings = Settings()
        whisper_mod_key = "ailine_runtime.adapters.media.whisper_stt"
        saved = sys.modules.get(whisper_mod_key)

        try:
            # Block the container's lazy import of the whisper_stt module
            sys.modules[whisper_mod_key] = None  # type: ignore[assignment]
            stt, _tts, _describer, _ocr = _build_media(settings)
        finally:
            if saved is not None:
                sys.modules[whisper_mod_key] = saved
            else:
                sys.modules.pop(whisper_mod_key, None)

        assert type(stt).__name__ == "FakeSTT"

    def test_whisper_stt_when_available(self):
        """No OpenAI key + faster_whisper available -> WhisperSTT.

        Note: faster_whisper is NOT installed, but WhisperSTT's __init__
        does not import it (lazy load in _ensure_model).  So the container's
        ``from ..adapters.media.whisper_stt import WhisperSTT`` succeeds.
        """
        settings = Settings()
        stt, _, _, _ = _build_media(settings)
        # WhisperSTT loads fine even without faster_whisper installed
        # because it does lazy import inside _ensure_model.
        assert type(stt).__name__ == "WhisperSTT"

    def test_fake_tts_when_no_key(self):
        settings = Settings()
        _, tts, _, _ = _build_media(settings)
        from ailine_runtime.adapters.media.fake_tts import FakeTTS

        assert isinstance(tts, FakeTTS)

    def test_ocr_always_created(self):
        settings = Settings()
        _, _, _, ocr = _build_media(settings)
        from ailine_runtime.adapters.media.ocr_processor import OCRProcessor

        assert isinstance(ocr, OCRProcessor)

    def test_openai_stt_import_error_fallback(self, monkeypatch: pytest.MonkeyPatch):
        """When openai_stt import fails at container level, fall back to FakeSTT."""
        settings = _settings_with_env_keys(monkeypatch, openai="sk-oai-test")
        openai_stt_key = "ailine_runtime.adapters.media.openai_stt"
        saved = sys.modules.get(openai_stt_key)

        try:
            # Block the container's lazy import of openai_stt module
            sys.modules[openai_stt_key] = None  # type: ignore[assignment]
            stt, _, _, _ = _build_media(settings)
        finally:
            if saved is not None:
                sys.modules[openai_stt_key] = saved
            else:
                sys.modules.pop(openai_stt_key, None)

        assert type(stt).__name__ == "FakeSTT"


# ===========================================================================
# TestBuildSignRecognition
# ===========================================================================


class TestBuildSignRecognition:
    def test_no_model_path(self):
        settings = Settings()
        sr = _build_sign_recognition(settings)
        from ailine_runtime.adapters.media.fake_sign_recognition import (
            FakeSignRecognition,
        )

        assert isinstance(sr, FakeSignRecognition)

    def test_model_path_import_error(self):
        with patch.dict(sys.modules, {"mediapipe": None}):
            settings = Settings(sign_model_path="/fake/path.tflite")
            sr = _build_sign_recognition(settings)
        from ailine_runtime.adapters.media.fake_sign_recognition import (
            FakeSignRecognition,
        )

        assert isinstance(sr, FakeSignRecognition)


# ===========================================================================
# TestResolveApiKey
# ===========================================================================


class TestResolveApiKey:
    def test_known_providers(self, monkeypatch: pytest.MonkeyPatch):
        settings = _settings_with_env_keys(
            monkeypatch,
            anthropic="ant",
            openai="oai",
            google="goo",
            openrouter="ort",
        )
        assert _resolve_api_key(settings, "anthropic") == "ant"
        assert _resolve_api_key(settings, "openai") == "oai"
        assert _resolve_api_key(settings, "gemini") == "goo"
        assert _resolve_api_key(settings, "openrouter") == "ort"

    def test_unknown_provider(self):
        settings = Settings()
        assert _resolve_api_key(settings, "unknown") == ""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _raise_import_error(*_args, **_kwargs):
    raise ImportError("mocked import failure")
