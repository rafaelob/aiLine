"""Port: media processing protocols (STT, TTS, sign recognition, image description)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class STT(Protocol):
    """Speech-to-text protocol."""

    async def transcribe(self, audio_bytes: bytes, *, language: str = "pt") -> str: ...


@runtime_checkable
class TTS(Protocol):
    """Text-to-speech protocol."""

    async def synthesize(self, text: str, *, locale: str = "pt-BR", speed: float = 1.0) -> bytes: ...


@runtime_checkable
class SignRecognition(Protocol):
    """Sign language recognition protocol."""

    async def recognize(self, video_bytes: bytes) -> dict: ...


@runtime_checkable
class ImageDescriber(Protocol):
    """Image description for alt-text generation."""

    async def describe(self, image_bytes: bytes, *, locale: str = "pt-BR") -> str: ...


@runtime_checkable
class OCRProcessor(Protocol):
    """OCR text extraction from PDF and image files.

    Implementations should handle graceful degradation when underlying
    libraries (pypdf, pytesseract) are not installed, returning a
    diagnostic message instead of raising.
    """

    async def extract_text(self, file_bytes: bytes, *, file_type: str = "pdf") -> str: ...
