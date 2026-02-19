"""Comprehensive tests for the TTS subsystem (F-165).

Covers:
- VoiceInfo dataclass
- TTS protocol conformance (FakeTTS and ElevenLabsTTS)
- FakeTTS adapter behavior (synthesize, list_voices, get_voice)
- ElevenLabsTTS adapter (mocked httpx)
- TTS API router endpoints (/v1/tts/*)
- Error handling and edge cases
"""

from __future__ import annotations

import struct
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from ailine_runtime.adapters.media.fake_tts import _FAKE_VOICES, FakeTTS
from ailine_runtime.domain.ports.media import TTS, VoiceInfo

# ===========================================================================
# 1. VoiceInfo dataclass tests
# ===========================================================================


class TestVoiceInfo:
    def test_create_with_defaults(self):
        vi = VoiceInfo(id="v1", name="Test Voice")
        assert vi.id == "v1"
        assert vi.name == "Test Voice"
        assert vi.language == "en"
        assert vi.gender == "neutral"
        assert vi.preview_url == ""
        assert vi.labels == {}

    def test_create_with_all_fields(self):
        vi = VoiceInfo(
            id="v2",
            name="Clara",
            language="pt-BR",
            gender="female",
            preview_url="https://example.com/preview.mp3",
            labels={"accent": "brazilian"},
        )
        assert vi.language == "pt-BR"
        assert vi.gender == "female"
        assert vi.labels["accent"] == "brazilian"

    def test_frozen(self):
        vi = VoiceInfo(id="v1", name="Test")
        with pytest.raises(AttributeError):
            vi.id = "other"  # type: ignore[misc]

    def test_equality(self):
        a = VoiceInfo(id="v1", name="Test", language="en")
        b = VoiceInfo(id="v1", name="Test", language="en")
        assert a == b

    def test_inequality(self):
        a = VoiceInfo(id="v1", name="Test")
        b = VoiceInfo(id="v2", name="Other")
        assert a != b


# ===========================================================================
# 2. TTS protocol conformance
# ===========================================================================


class TestProtocolConformance:
    def test_fake_tts_is_tts_protocol(self):
        assert isinstance(FakeTTS(), TTS)

    def test_elevenlabs_is_tts_protocol(self):
        from ailine_runtime.adapters.media.elevenlabs_tts import ElevenLabsTTS

        adapter = ElevenLabsTTS(api_key="test-key")
        assert isinstance(adapter, TTS)


# ===========================================================================
# 3. FakeTTS adapter tests
# ===========================================================================


class TestFakeTTS:
    @pytest.fixture()
    def tts(self) -> FakeTTS:
        return FakeTTS()

    @pytest.mark.asyncio
    async def test_synthesize_returns_wav(self, tts: FakeTTS):
        audio = await tts.synthesize("Hello world")
        # Valid WAV header starts with RIFF
        assert audio[:4] == b"RIFF"
        assert audio[8:12] == b"WAVE"

    @pytest.mark.asyncio
    async def test_synthesize_custom_duration(self):
        tts = FakeTTS(duration_ms=500)
        audio = await tts.synthesize("Test")
        # Longer duration = more data bytes
        assert len(audio) > 100

    @pytest.mark.asyncio
    async def test_synthesize_wav_structure(self, tts: FakeTTS):
        audio = await tts.synthesize("Test")
        # Parse WAV header
        assert audio[:4] == b"RIFF"
        file_size = struct.unpack_from("<I", audio, 4)[0]
        assert file_size == len(audio) - 8

    @pytest.mark.asyncio
    async def test_list_voices_all(self, tts: FakeTTS):
        voices = await tts.list_voices()
        assert len(voices) == len(_FAKE_VOICES)
        assert all(isinstance(v, VoiceInfo) for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_filter_english(self, tts: FakeTTS):
        voices = await tts.list_voices(language="en")
        assert len(voices) >= 2
        assert all("en" in v.language.lower() for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_filter_portuguese(self, tts: FakeTTS):
        voices = await tts.list_voices(language="pt")
        assert len(voices) >= 1
        assert all("pt" in v.language.lower() for v in voices)

    @pytest.mark.asyncio
    async def test_list_voices_filter_no_match(self, tts: FakeTTS):
        voices = await tts.list_voices(language="ja")
        assert voices == []

    @pytest.mark.asyncio
    async def test_get_voice_found(self, tts: FakeTTS):
        voice = await tts.get_voice("fake-voice-en-female")
        assert voice is not None
        assert voice.name == "Aria (Fake)"
        assert voice.gender == "female"

    @pytest.mark.asyncio
    async def test_get_voice_not_found(self, tts: FakeTTS):
        voice = await tts.get_voice("nonexistent-voice-id")
        assert voice is None

    @pytest.mark.asyncio
    async def test_list_voices_returns_copy(self, tts: FakeTTS):
        """Ensure list_voices returns a new list each time."""
        a = await tts.list_voices()
        b = await tts.list_voices()
        assert a is not b


# ===========================================================================
# 4. ElevenLabsTTS adapter tests (mocked httpx)
# ===========================================================================


class TestElevenLabsTTSMocked:
    @pytest.fixture()
    def adapter(self):
        from ailine_runtime.adapters.media.elevenlabs_tts import ElevenLabsTTS

        return ElevenLabsTTS(api_key="test-key-123", voice_id="voice-abc")

    @pytest.mark.asyncio
    async def test_synthesize_success(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"\xff\xfb\x90\x00"  # fake mpeg bytes
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await adapter.synthesize("Hello")
            assert result == b"\xff\xfb\x90\x00"
            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args
            assert "voice-abc" in call_kwargs.args[0]

    @pytest.mark.asyncio
    async def test_synthesize_uses_model_id(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"audio"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            await adapter.synthesize("Test")
            payload = mock_client.post.call_args.kwargs.get("json", {})
            assert payload["model_id"] == "eleven_v3"

    @pytest.mark.asyncio
    async def test_list_voices_parses_response(self, adapter):
        api_response = {
            "voices": [
                {
                    "voice_id": "v1",
                    "name": "Rachel",
                    "labels": {"language": "english", "gender": "female"},
                    "preview_url": "https://example.com/rachel.mp3",
                },
                {
                    "voice_id": "v2",
                    "name": "Pedro",
                    "labels": {"language": "portuguese", "gender": "male"},
                    "preview_url": "",
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=api_response)
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            voices = await adapter.list_voices()
            assert len(voices) == 2
            assert voices[0].id == "v1"
            assert voices[0].name == "Rachel"
            assert voices[1].gender == "male"

    @pytest.mark.asyncio
    async def test_list_voices_filter_by_language(self, adapter):
        api_response = {
            "voices": [
                {
                    "voice_id": "v1",
                    "name": "Rachel",
                    "labels": {"language": "english"},
                    "preview_url": "",
                },
                {
                    "voice_id": "v2",
                    "name": "Pedro",
                    "labels": {"language": "portuguese"},
                    "preview_url": "",
                },
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=api_response)
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            voices = await adapter.list_voices(language="portuguese")
            assert len(voices) == 1
            assert voices[0].name == "Pedro"

    @pytest.mark.asyncio
    async def test_get_voice_success(self, adapter):
        api_response = {
            "voice_id": "v1",
            "name": "Rachel",
            "labels": {"language": "english", "gender": "female"},
            "preview_url": "https://example.com/r.mp3",
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=api_response)
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            voice = await adapter.get_voice("v1")
            assert voice is not None
            assert voice.id == "v1"
            assert voice.name == "Rachel"

    @pytest.mark.asyncio
    async def test_get_voice_not_found(self, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            voice = await adapter.get_voice("nonexistent")
            assert voice is None


# ===========================================================================
# 5. TTS API router tests
# ===========================================================================

# Minimal app factory for testing the TTS router in isolation.


def _fake_auth() -> str:
    """Dependency override that bypasses auth and returns a fake teacher ID."""
    return "teacher-test-1"


def _make_test_app(tts_adapter: TTS | None = None) -> FastAPI:
    """Build a minimal FastAPI app with the TTS router and bypassed auth."""
    from ailine_runtime.api.routers.tts import router
    from ailine_runtime.app.authz import require_teacher_or_admin

    app = FastAPI()

    # Fake container
    container = MagicMock()
    container.tts = tts_adapter
    app.state.container = container

    # Override auth dependency to bypass tenant context requirement
    app.dependency_overrides[require_teacher_or_admin] = _fake_auth

    app.include_router(router, prefix="/v1/tts")
    return app


@pytest.fixture()
def fake_tts() -> FakeTTS:
    return FakeTTS()


@pytest.fixture()
def app_with_tts(fake_tts: FakeTTS) -> FastAPI:
    """App with FakeTTS and bypassed auth."""
    return _make_test_app(fake_tts)


@pytest.fixture()
def app_without_tts() -> FastAPI:
    """App with no TTS adapter configured."""
    return _make_test_app(None)


class TestTTSRouter:
    @pytest.mark.asyncio
    async def test_synthesize_returns_audio(self, app_with_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_tts),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/v1/tts/synthesize",
                json={"text": "Hello world", "language": "en"},
            )
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "audio/wav"
            assert resp.content[:4] == b"RIFF"

    @pytest.mark.asyncio
    async def test_synthesize_validates_text_empty(self, app_with_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_tts),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/v1/tts/synthesize",
                json={"text": ""},
            )
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_synthesize_validates_speed_range(self, app_with_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_tts),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/v1/tts/synthesize",
                json={"text": "Hello", "speed": 10.0},
            )
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_voices(self, app_with_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_tts),
            base_url="http://test",
        ) as client:
            resp = await client.get("/v1/tts/voices")
            assert resp.status_code == 200
            data = resp.json()
            assert "voices" in data
            assert "total" in data
            assert data["total"] == len(_FAKE_VOICES)
            assert len(data["voices"]) == len(_FAKE_VOICES)

    @pytest.mark.asyncio
    async def test_list_voices_filter(self, app_with_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_tts),
            base_url="http://test",
        ) as client:
            resp = await client.get("/v1/tts/voices?language=pt")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] >= 1
            for voice in data["voices"]:
                assert "pt" in voice["language"].lower()

    @pytest.mark.asyncio
    async def test_get_voice_found(self, app_with_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_tts),
            base_url="http://test",
        ) as client:
            resp = await client.get("/v1/tts/voices/fake-voice-en-female")
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == "fake-voice-en-female"
            assert data["name"] == "Aria (Fake)"

    @pytest.mark.asyncio
    async def test_get_voice_not_found(self, app_with_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_tts),
            base_url="http://test",
        ) as client:
            resp = await client.get("/v1/tts/voices/nonexistent")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_synthesize_no_adapter_503(self, app_without_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_without_tts),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/v1/tts/synthesize",
                json={"text": "Hello"},
            )
            assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_list_voices_no_adapter_503(self, app_without_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_without_tts),
            base_url="http://test",
        ) as client:
            resp = await client.get("/v1/tts/voices")
            assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_get_voice_no_adapter_503(self, app_without_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_without_tts),
            base_url="http://test",
        ) as client:
            resp = await client.get("/v1/tts/voices/fake-voice-en-female")
            assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_synthesize_text_too_long(self, app_with_tts: FastAPI):
        async with AsyncClient(
            transport=ASGITransport(app=app_with_tts),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/v1/tts/synthesize",
                json={"text": "x" * 5001},
            )
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_voice_response_schema(self, app_with_tts: FastAPI):
        """Verify the voice response includes all expected fields."""
        async with AsyncClient(
            transport=ASGITransport(app=app_with_tts),
            base_url="http://test",
        ) as client:
            resp = await client.get("/v1/tts/voices/fake-voice-pt-female")
            assert resp.status_code == 200
            data = resp.json()
            expected_keys = {"id", "name", "language", "gender", "preview_url", "labels"}
            assert set(data.keys()) == expected_keys
            assert data["language"] == "pt-BR"
            assert data["gender"] == "female"


# ===========================================================================
# 6. ExportFormat AUDIO_MP3 test
# ===========================================================================


class TestExportFormatAudioMp3:
    def test_audio_mp3_exists(self):
        from ailine_runtime.domain.entities.plan import ExportFormat

        assert ExportFormat.AUDIO_MP3 == "audio_mp3"
        assert "audio_mp3" in [e.value for e in ExportFormat]
