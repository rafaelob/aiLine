"""Port: media processing protocols (STT, TTS, sign recognition, image description)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@runtime_checkable
class STT(Protocol):
    """Speech-to-text protocol."""

    async def transcribe(self, audio_bytes: bytes, *, language: str = "pt") -> str: ...


@dataclass(frozen=True)
class VoiceInfo:
    """Metadata about an available TTS voice.

    Attributes:
        id: Provider-specific voice identifier.
        name: Human-readable display name.
        language: Primary BCP-47 language code (e.g. "en", "pt-BR").
        gender: Voice gender hint ("male", "female", "neutral").
        preview_url: Optional URL to a sample audio clip.
        labels: Additional provider-specific labels.
    """

    id: str
    name: str
    language: str = "en"
    gender: str = "neutral"
    preview_url: str = ""
    labels: dict[str, str] = field(default_factory=dict)


@runtime_checkable
class TTS(Protocol):
    """Text-to-speech protocol."""

    async def synthesize(
        self, text: str, *, locale: str = "pt-BR", speed: float = 1.0
    ) -> bytes: ...

    async def list_voices(self, *, language: str | None = None) -> list[VoiceInfo]: ...

    async def get_voice(self, voice_id: str) -> VoiceInfo | None: ...


@runtime_checkable
class SignRecognition(Protocol):
    """Sign language recognition protocol."""

    async def recognize(self, video_bytes: bytes) -> dict: ...


@runtime_checkable
class ImageDescriber(Protocol):
    """Image description for alt-text generation."""

    async def describe(self, image_bytes: bytes, *, locale: str = "pt-BR") -> str: ...


@runtime_checkable
class ImageGenerator(Protocol):
    """AI image generation for educational illustrations."""

    async def generate(
        self,
        prompt: str,
        *,
        aspect_ratio: str = "16:9",
        style: str = "educational_illustration",
        size: str = "1K",
    ) -> bytes: ...


@runtime_checkable
class OCRProcessor(Protocol):
    """OCR text extraction from PDF and image files.

    Implementations should handle graceful degradation when underlying
    libraries (pypdf, pytesseract) are not installed, returning a
    diagnostic message instead of raising.
    """

    async def extract_text(
        self, file_bytes: bytes, *, file_type: str = "pdf"
    ) -> str: ...
