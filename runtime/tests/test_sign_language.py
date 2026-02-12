"""Tests for sign language adapters and API endpoints.

Covers:
- FakeSignRecognition: deterministic output, custom responses, protocol conformance
- MediaPipeSignRecognition: placeholder behavior, graceful degradation
- Sign language API endpoints: /sign-language/recognize, /sign-language/gestures
- Container wiring: sign_recognition field populated correctly

These tests run entirely without external models or APIs (ADR-051).
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from httpx import ASGITransport, AsyncClient

from ailine_runtime.adapters.media.fake_sign_recognition import FakeSignRecognition
from ailine_runtime.adapters.media.sign_recognition import MediaPipeSignRecognition
from ailine_runtime.domain.ports.media import SignRecognition

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_recognizer() -> FakeSignRecognition:
    return FakeSignRecognition()


@pytest.fixture
def fake_recognizer_custom() -> FakeSignRecognition:
    return FakeSignRecognition(
        responses=[
            {"gesture": "oi", "confidence": 0.99, "landmarks": [], "model": "custom"},
            {"gesture": "sim", "confidence": 0.80, "landmarks": [], "model": "custom"},
        ]
    )


@pytest.fixture
def mediapipe_recognizer() -> MediaPipeSignRecognition:
    return MediaPipeSignRecognition()


@pytest.fixture
def mediapipe_recognizer_with_path() -> MediaPipeSignRecognition:
    return MediaPipeSignRecognition(model_path="/fake/model.onnx")


@pytest.fixture
def app():
    """Create a test FastAPI app with FakeSignRecognition wired in."""
    from ailine_runtime.api.app import create_app
    from ailine_runtime.shared.config import Settings

    settings = Settings()
    application = create_app(settings)
    # Ensure the container has a FakeSignRecognition adapter
    application.state.container = replace(
        application.state.container,
        sign_recognition=FakeSignRecognition(),
    )
    return application


@pytest.fixture
async def client(app):
    """Async HTTP client for the FastAPI test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ===========================================================================
# FakeSignRecognition -- Protocol Conformance
# ===========================================================================


class TestFakeSignRecognitionProtocol:
    """Verify FakeSignRecognition satisfies the SignRecognition protocol."""

    def test_is_runtime_checkable(self, fake_recognizer: FakeSignRecognition):
        assert isinstance(fake_recognizer, SignRecognition)

    async def test_recognize_returns_dict(self, fake_recognizer: FakeSignRecognition):
        result = await fake_recognizer.recognize(b"\x00" * 10)
        assert isinstance(result, dict)

    async def test_result_has_required_keys(
        self, fake_recognizer: FakeSignRecognition
    ):
        result = await fake_recognizer.recognize(b"\x00" * 10)
        assert "gesture" in result
        assert "confidence" in result
        assert "landmarks" in result
        assert "model" in result


# ===========================================================================
# FakeSignRecognition -- Behavior
# ===========================================================================


class TestFakeSignRecognitionBehavior:
    """Verify FakeSignRecognition deterministic output and cycling."""

    async def test_deterministic_gesture_selection(
        self, fake_recognizer: FakeSignRecognition
    ):
        """Gesture is determined by input byte length modulo number of gestures."""
        # 4 gestures: oi(0), obrigado(1), sim(2), nao(3)
        r0 = await fake_recognizer.recognize(b"\x00" * 4)  # 4 % 4 = 0 -> oi
        assert r0["gesture"] == "oi"

        r1 = await fake_recognizer.recognize(b"\x00" * 5)  # 5 % 4 = 1 -> obrigado
        assert r1["gesture"] == "obrigado"

        r2 = await fake_recognizer.recognize(b"\x00" * 6)  # 6 % 4 = 2 -> sim
        assert r2["gesture"] == "sim"

        r3 = await fake_recognizer.recognize(b"\x00" * 7)  # 7 % 4 = 3 -> nao
        assert r3["gesture"] == "nao"

    async def test_wraps_around(self, fake_recognizer: FakeSignRecognition):
        """Gesture selection wraps for input lengths > number of gestures."""
        r8 = await fake_recognizer.recognize(b"\x00" * 8)  # 8 % 4 = 0 -> oi
        assert r8["gesture"] == "oi"

    async def test_empty_input(self, fake_recognizer: FakeSignRecognition):
        """Empty bytes yield gesture index 0 (0 % 4 = 0)."""
        result = await fake_recognizer.recognize(b"")
        assert result["gesture"] == "oi"

    async def test_default_confidence(self, fake_recognizer: FakeSignRecognition):
        result = await fake_recognizer.recognize(b"\x00")
        assert result["confidence"] == 0.95

    async def test_custom_confidence(self):
        recognizer = FakeSignRecognition(confidence=0.50)
        result = await recognizer.recognize(b"\x00")
        assert result["confidence"] == 0.50

    async def test_model_is_fake(self, fake_recognizer: FakeSignRecognition):
        result = await fake_recognizer.recognize(b"\x00")
        assert result["model"] == "fake"

    async def test_landmarks_empty(self, fake_recognizer: FakeSignRecognition):
        result = await fake_recognizer.recognize(b"\x00")
        assert result["landmarks"] == []

    async def test_custom_responses_cycle(
        self, fake_recognizer_custom: FakeSignRecognition
    ):
        r1 = await fake_recognizer_custom.recognize(b"\x00")
        r2 = await fake_recognizer_custom.recognize(b"\x00")
        r3 = await fake_recognizer_custom.recognize(b"\x00")
        assert r1["gesture"] == "oi"
        assert r2["gesture"] == "sim"
        assert r3["gesture"] == "oi"  # cycles back

    async def test_custom_responses_preserve_all_fields(
        self, fake_recognizer_custom: FakeSignRecognition
    ):
        result = await fake_recognizer_custom.recognize(b"\x00")
        assert result["confidence"] == 0.99
        assert result["model"] == "custom"

    def test_gestures_class_attribute(self):
        """GESTURES class attribute matches the canonical MVP list."""
        assert FakeSignRecognition.GESTURES == ["oi", "obrigado", "sim", "nao"]

    async def test_call_count_increments(
        self, fake_recognizer: FakeSignRecognition
    ):
        assert fake_recognizer._call_count == 0
        await fake_recognizer.recognize(b"\x00")
        assert fake_recognizer._call_count == 1
        await fake_recognizer.recognize(b"\x00")
        assert fake_recognizer._call_count == 2


# ===========================================================================
# MediaPipeSignRecognition -- Placeholder Behavior
# ===========================================================================


class TestMediaPipeSignRecognitionProtocol:
    """Verify MediaPipeSignRecognition satisfies the SignRecognition protocol."""

    def test_is_runtime_checkable(
        self, mediapipe_recognizer: MediaPipeSignRecognition
    ):
        assert isinstance(mediapipe_recognizer, SignRecognition)

    async def test_recognize_returns_dict(
        self, mediapipe_recognizer: MediaPipeSignRecognition
    ):
        result = await mediapipe_recognizer.recognize(b"\x00" * 10)
        assert isinstance(result, dict)


class TestMediaPipeSignRecognitionBehavior:
    """Verify the placeholder always returns 'unknown' with zero confidence."""

    async def test_returns_unknown(
        self, mediapipe_recognizer: MediaPipeSignRecognition
    ):
        result = await mediapipe_recognizer.recognize(b"\x00" * 50)
        assert result["gesture"] == "unknown"

    async def test_zero_confidence(
        self, mediapipe_recognizer: MediaPipeSignRecognition
    ):
        result = await mediapipe_recognizer.recognize(b"\x00" * 50)
        assert result["confidence"] == 0.0

    async def test_model_identifier(
        self, mediapipe_recognizer: MediaPipeSignRecognition
    ):
        result = await mediapipe_recognizer.recognize(b"\x00")
        assert result["model"] == "mediapipe-mlp-placeholder"

    async def test_includes_note(
        self, mediapipe_recognizer: MediaPipeSignRecognition
    ):
        result = await mediapipe_recognizer.recognize(b"\x00")
        assert "note" in result
        assert "training data" in result["note"]

    async def test_empty_landmarks(
        self, mediapipe_recognizer: MediaPipeSignRecognition
    ):
        result = await mediapipe_recognizer.recognize(b"\x00")
        assert result["landmarks"] == []

    async def test_empty_input(
        self, mediapipe_recognizer: MediaPipeSignRecognition
    ):
        """Empty bytes should still return a valid result, not crash."""
        result = await mediapipe_recognizer.recognize(b"")
        assert result["gesture"] == "unknown"

    def test_model_path_defaults_to_none(self):
        recognizer = MediaPipeSignRecognition()
        assert recognizer._model_path is None

    def test_model_path_stored(
        self, mediapipe_recognizer_with_path: MediaPipeSignRecognition
    ):
        assert mediapipe_recognizer_with_path._model_path == "/fake/model.onnx"

    def test_try_load_model_exception_handled_gracefully(self):
        """When _try_load_model raises an exception, it is caught (lines 56-57)."""
        from unittest.mock import patch

        with patch.object(
            MediaPipeSignRecognition,
            "_try_load_model",
            side_effect=RuntimeError("model load boom"),
        ):
            # The constructor calls _try_load_model when model_path is set;
            # but we need to test the real exception path inside _try_load_model.
            pass

        # Test the actual except branch: force the try block to raise
        recognizer = MediaPipeSignRecognition.__new__(MediaPipeSignRecognition)
        recognizer._model_path = "/bad/path"
        recognizer._model_loaded = False

        # Patch the logger.info call inside _try_load_model to raise
        with patch(
            "ailine_runtime.adapters.media.sign_recognition.logger"
        ) as mock_logger:
            mock_logger.info.side_effect = Exception("unexpected error")
            # This should catch the exception and call logger.warning
            recognizer._try_load_model()
            mock_logger.warning.assert_called_once()


# ===========================================================================
# Sign Language API Endpoints
# ===========================================================================


class TestRecognizeEndpoint:
    """Test POST /sign-language/recognize."""

    async def test_recognize_success(self, client: AsyncClient):
        response = await client.post(
            "/sign-language/recognize",
            files={"file": ("gesture.webm", b"\x00" * 100, "video/webm")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "gesture" in data
        assert "confidence" in data
        assert "model" in data
        assert data["model"] == "fake"

    async def test_recognize_returns_valid_gesture(self, client: AsyncClient):
        """The returned gesture must be one of the 4 MVP gestures."""
        response = await client.post(
            "/sign-language/recognize",
            files={"file": ("gesture.webm", b"\x00" * 5, "video/webm")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["gesture"] in ["oi", "obrigado", "sim", "nao"]

    async def test_recognize_deterministic(self, client: AsyncClient):
        """Same input bytes -> same gesture (deterministic fake)."""
        payload = b"\x00" * 42
        r1 = await client.post(
            "/sign-language/recognize",
            files={"file": ("a.webm", payload, "video/webm")},
        )
        r2 = await client.post(
            "/sign-language/recognize",
            files={"file": ("b.webm", payload, "video/webm")},
        )
        assert r1.json()["gesture"] == r2.json()["gesture"]

    async def test_recognize_empty_file_returns_400(self, client: AsyncClient):
        response = await client.post(
            "/sign-language/recognize",
            files={"file": ("empty.webm", b"", "video/webm")},
        )
        assert response.status_code == 400

    async def test_recognize_accepts_image(self, client: AsyncClient):
        """Should also accept image files (single frame)."""
        response = await client.post(
            "/sign-language/recognize",
            files={"file": ("frame.png", b"\x89PNG" + b"\x00" * 50, "image/png")},
        )
        assert response.status_code == 200

    async def test_recognize_confidence_in_range(self, client: AsyncClient):
        response = await client.post(
            "/sign-language/recognize",
            files={"file": ("g.webm", b"\x00" * 10, "video/webm")},
        )
        data = response.json()
        assert 0.0 <= data["confidence"] <= 1.0


class TestGesturesEndpoint:
    """Test GET /sign-language/gestures."""

    async def test_gestures_list(self, client: AsyncClient):
        response = await client.get("/sign-language/gestures")
        assert response.status_code == 200
        data = response.json()
        assert "gestures" in data
        assert "model" in data
        assert "note" in data

    async def test_gestures_count(self, client: AsyncClient):
        response = await client.get("/sign-language/gestures")
        gestures = response.json()["gestures"]
        assert len(gestures) == 4

    async def test_gestures_ids(self, client: AsyncClient):
        response = await client.get("/sign-language/gestures")
        ids = [g["id"] for g in response.json()["gestures"]]
        assert set(ids) == {"oi", "obrigado", "sim", "nao"}

    async def test_gestures_have_multilingual_names(self, client: AsyncClient):
        response = await client.get("/sign-language/gestures")
        for gesture in response.json()["gestures"]:
            assert "name_pt" in gesture
            assert "name_en" in gesture
            assert "name_es" in gesture

    async def test_gestures_model_field(self, client: AsyncClient):
        response = await client.get("/sign-language/gestures")
        assert response.json()["model"] == "mediapipe-mlp"

    async def test_gestures_note_field(self, client: AsyncClient):
        response = await client.get("/sign-language/gestures")
        note = response.json()["note"]
        assert "MVP" in note


# ===========================================================================
# Container Wiring
# ===========================================================================


class TestContainerSignRecognition:
    """Verify the DI container builds sign_recognition correctly."""

    def test_container_has_sign_recognition(self, settings):
        from ailine_runtime.shared.container import Container

        container = Container.build(settings)
        assert container.sign_recognition is not None

    def test_container_default_is_fake(self, settings):
        from ailine_runtime.shared.container import Container

        container = Container.build(settings)
        assert isinstance(container.sign_recognition, FakeSignRecognition)

    async def test_container_sign_recognition_works(self, settings):
        from ailine_runtime.shared.container import Container

        container = Container.build(settings)
        result = await container.sign_recognition.recognize(b"\x00" * 10)
        assert "gesture" in result


# ===========================================================================
# Sign Recognition Adapter Not Configured (503)
# ===========================================================================


class TestRecognizeWithoutAdapter:
    """Verify 503 when sign_recognition is None on the container."""

    @pytest.fixture
    def app_no_sign(self):
        from ailine_runtime.api.app import create_app
        from ailine_runtime.shared.config import Settings

        settings = Settings()
        application = create_app(settings)
        application.state.container = replace(
            application.state.container,
            sign_recognition=None,
        )
        return application

    @pytest.fixture
    async def client_no_sign(self, app_no_sign):
        transport = ASGITransport(app=app_no_sign)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    async def test_recognize_returns_503(self, client_no_sign: AsyncClient):
        response = await client_no_sign.post(
            "/sign-language/recognize",
            files={"file": ("g.webm", b"\x00" * 10, "video/webm")},
        )
        assert response.status_code == 503
