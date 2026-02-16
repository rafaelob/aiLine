"""Media adapters: STT, TTS, image description, image generation, OCR, sign recognition.

Fake implementations are always available for testing.
Real implementations require optional dependencies (see pyproject.toml).
"""

from .fake_image_describer import FakeImageDescriber
from .fake_image_gen import FakeImageGenerator
from .fake_sign_recognition import FakeSignRecognition
from .fake_stt import FakeSTT
from .fake_tts import FakeTTS
from .ocr_processor import OCRProcessor

__all__ = [
    "FakeImageDescriber",
    "FakeImageGenerator",
    "FakeSTT",
    "FakeSignRecognition",
    "FakeTTS",
    "OCRProcessor",
    # Real adapters (lazy-import; not re-exported here to avoid
    # import errors when optional dependencies are missing):
    #   WhisperSTT              -> .whisper_stt
    #   OpenAISTT               -> .openai_stt
    #   ElevenLabsTTS           -> .elevenlabs_tts
    #   GeminiImageGenerator    -> .gemini_image_gen
    #   MediaPipeSignRecognition -> .sign_recognition
]
