"""Media API router -- STT, TTS, image description, OCR endpoints.

All endpoints resolve their adapter from ``app.state.container``.
When no real adapter is configured the container falls back to the
fake implementations, which keeps the API surface testable without
external services.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ...app.authz import require_authenticated

logger = structlog.get_logger(__name__)

router = APIRouter()

# -- File upload size limits ---------------------------------------------------

MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50 MB


# -- Request / Response schemas -----------------------------------------------


class SynthesizeRequest(BaseModel):
    text: str = Field(
        ..., min_length=1, max_length=5000, description="Text to synthesize."
    )
    locale: str = Field("pt-BR", description="BCP-47 locale tag.")
    speed: float = Field(1.0, ge=0.25, le=4.0, description="Playback speed multiplier.")


class TranscriptionResponse(BaseModel):
    text: str


class DescriptionResponse(BaseModel):
    description: str


class ImageGenRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Description of the image to generate.",
    )
    aspect_ratio: str = Field(
        "16:9", description="Aspect ratio: 1:1, 3:4, 4:3, 9:16, 16:9."
    )
    style: str = Field(
        "educational_illustration",
        description="Style template: educational_illustration, infographic, diagram, cartoon, photo_realistic.",
    )
    size: str = Field("1K", description='Output resolution: "1K" or "2K".')


class ExtractedTextResponse(BaseModel):
    text: str
    file_type: str


# -- Helper to resolve adapters -----------------------------------------------


def _get_adapter(request: Request, name: str) -> Any:
    """Retrieve a media adapter from the DI container.

    Raises 503 if the adapter is not configured.
    """
    container = request.app.state.container
    adapter = getattr(container, name, None)
    if adapter is None:
        raise HTTPException(
            status_code=503,
            detail=f"Media adapter '{name}' is not configured.",
        )
    return adapter


# -- Endpoints ----------------------------------------------------------------


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    request: Request,
    file: UploadFile,
    language: str = "pt",
) -> TranscriptionResponse:
    """Transcribe an audio file to text (STT)."""
    require_authenticated()
    stt = _get_adapter(request, "stt")
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file.")
    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Maximum audio size: 10MB."
        )
    logger.info("media.transcribe", language=language, size=len(audio_bytes))
    text = await stt.transcribe(audio_bytes, language=language)
    return TranscriptionResponse(text=text)


@router.post("/synthesize")
async def synthesize_speech(
    request: Request,
    body: SynthesizeRequest,
) -> Response:
    """Synthesize text to audio (TTS).

    Returns raw audio bytes with an appropriate content type.
    """
    require_authenticated()
    tts = _get_adapter(request, "tts")
    logger.info(
        "media.synthesize",
        locale=body.locale,
        speed=body.speed,
        text_length=len(body.text),
    )
    audio_bytes = await tts.synthesize(body.text, locale=body.locale, speed=body.speed)
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": "inline; filename=speech.wav"},
    )


@router.post("/describe-image", response_model=DescriptionResponse)
async def describe_image(
    request: Request,
    file: UploadFile,
    locale: str = "pt-BR",
) -> DescriptionResponse:
    """Generate an alt-text description for an uploaded image."""
    require_authenticated()
    describer = _get_adapter(request, "image_describer")
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file.")
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Maximum image size: 5MB."
        )
    logger.info("media.describe_image", locale=locale, size=len(image_bytes))
    description = await describer.describe(image_bytes, locale=locale)
    return DescriptionResponse(description=description)


@router.post("/extract-text", response_model=ExtractedTextResponse)
async def extract_text(
    request: Request,
    file: UploadFile,
) -> ExtractedTextResponse:
    """Extract text from a PDF or image file (OCR).

    The file type is inferred from the upload's content type.
    """
    require_authenticated()
    ocr = _get_adapter(request, "ocr")
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(file_bytes) > MAX_DOCUMENT_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Maximum document size: 50MB."
        )

    content_type = file.content_type or ""
    file_type = "pdf" if "pdf" in content_type else "image"

    logger.info(
        "media.extract_text",
        file_type=file_type,
        content_type=content_type,
        size=len(file_bytes),
    )
    text = await ocr.extract_text(file_bytes, file_type=file_type)
    return ExtractedTextResponse(text=text, file_type=file_type)


@router.post("/generate-image")
async def generate_image(
    request: Request,
    body: ImageGenRequest,
) -> Response:
    """Generate an educational image from a text prompt (Imagen 4).

    Returns raw PNG bytes. Requires image_generator adapter to be configured.
    """
    require_authenticated()
    generator = _get_adapter(request, "image_generator")
    logger.info(
        "media.generate_image",
        style=body.style,
        aspect_ratio=body.aspect_ratio,
        size=body.size,
        prompt_length=len(body.prompt),
    )
    image_bytes = await generator.generate(
        body.prompt,
        aspect_ratio=body.aspect_ratio,
        style=body.style,
        size=body.size,
    )
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": "inline; filename=generated.png"},
    )
