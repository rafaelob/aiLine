"""Media API router -- STT, TTS, image description, OCR endpoints.

All endpoints resolve their adapter from ``app.state.container``.
When no real adapter is configured the container falls back to the
fake implementations, which keeps the API surface testable without
external services.
"""

from __future__ import annotations

from typing import Any, Literal

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ...accessibility.braille_translator import BrfConfig, text_to_brf_bytes
from ...app.authz import require_authenticated
from ...shared.sanitize import sanitize_prompt

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
    aspect_ratio: Literal["1:1", "3:4", "4:3", "9:16", "16:9"] = Field(
        "16:9", description="Aspect ratio: 1:1, 3:4, 4:3, 9:16, 16:9."
    )
    style: Literal[
        "educational_illustration",
        "infographic",
        "diagram",
        "cartoon",
        "photo_realistic",
    ] = Field(
        "educational_illustration",
        description="Style template: educational_illustration, infographic, diagram, cartoon, photo_realistic.",
    )
    size: str = Field("1K", description='Output resolution: "1K" or "2K".')


class ExtractedTextResponse(BaseModel):
    text: str
    file_type: str


class BrfExportRequest(BaseModel):
    text: str = Field(
        ..., min_length=1, max_length=50_000, description="Plain text to convert to BRF."
    )
    line_width: int = Field(40, ge=20, le=80, description="Cells per line (default 40).")
    page_height: int = Field(25, ge=10, le=50, description="Lines per page (default 25).")
    page_numbers: bool = Field(True, description="Include page number headers.")


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


def _check_content_length(request: Request, max_size: int, label: str) -> None:
    """Reject oversized uploads early using Content-Length header.

    This prevents reading the full body into memory before discovering
    it exceeds the limit. Falls through silently when the header is
    missing (multipart uploads may not include it).
    """
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum {label} size: {max_size // (1024 * 1024)}MB.",
        )


# -- Endpoints ----------------------------------------------------------------


def _validate_content_type(
    file: UploadFile,
    *,
    allowed_prefixes: tuple[str, ...],
    allowed_exact: tuple[str, ...] = (),
    label: str,
) -> None:
    """Validate that the uploaded file's content type is in the allowlist.

    Raises HTTP 415 if the content type does not match.
    """
    ct = (file.content_type or "").lower()
    if not ct:
        raise HTTPException(
            status_code=415,
            detail=f"Missing content type. Expected {label} file.",
        )
    for prefix in allowed_prefixes:
        if ct.startswith(prefix):
            return
    if ct in allowed_exact:
        return
    raise HTTPException(
        status_code=415,
        detail=f"Unsupported content type '{ct}'. Expected {label} file.",
    )


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    request: Request,
    file: UploadFile,
    language: str = "pt",
    _teacher_id: str = Depends(require_authenticated),
) -> TranscriptionResponse:
    """Transcribe an audio file to text (STT)."""
    _validate_content_type(file, allowed_prefixes=("audio/",), label="audio")
    _check_content_length(request, MAX_AUDIO_SIZE, "audio")
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
    _teacher_id: str = Depends(require_authenticated),
) -> Response:
    """Synthesize text to audio (TTS).

    Returns raw audio bytes with an appropriate content type.
    """
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
    _teacher_id: str = Depends(require_authenticated),
) -> DescriptionResponse:
    """Generate an alt-text description for an uploaded image."""
    _validate_content_type(file, allowed_prefixes=("image/",), label="image")
    _check_content_length(request, MAX_IMAGE_SIZE, "image")
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
    _teacher_id: str = Depends(require_authenticated),
) -> ExtractedTextResponse:
    """Extract text from a PDF or image file (OCR).

    The file type is inferred from the upload's content type.
    """
    _validate_content_type(
        file,
        allowed_prefixes=("image/",),
        allowed_exact=("application/pdf",),
        label="image or PDF",
    )
    _check_content_length(request, MAX_DOCUMENT_SIZE, "document")
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
    _teacher_id: str = Depends(require_authenticated),
) -> Response:
    """Generate an educational image from a text prompt (Imagen 4).

    Returns raw PNG bytes. Requires image_generator adapter to be configured.
    """
    generator = _get_adapter(request, "image_generator")
    # Sanitize prompt before passing to the image generator to strip
    # null bytes, normalize unicode, and enforce length limits.
    clean_prompt = sanitize_prompt(body.prompt, max_length=2000)
    logger.info(
        "media.generate_image",
        style=body.style,
        aspect_ratio=body.aspect_ratio,
        size=body.size,
        prompt_length=len(clean_prompt),
    )
    image_bytes = await generator.generate(
        clean_prompt,
        aspect_ratio=body.aspect_ratio,
        style=body.style,
        size=body.size,
    )
    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={"Content-Disposition": "inline; filename=generated.png"},
    )


@router.post("/export-brf")
async def export_braille_brf(
    body: BrfExportRequest,
    _teacher_id: str = Depends(require_authenticated),
) -> Response:
    """Convert plain text to BRF (Braille Ready Format).

    Returns an ASCII-encoded .brf file suitable for Braille embossers
    and Braille display software. Uses Grade 1 (uncontracted) translation.
    """
    config = BrfConfig(
        line_width=body.line_width,
        page_height=body.page_height,
        page_numbers=body.page_numbers,
    )
    logger.info(
        "media.export_brf",
        text_length=len(body.text),
        line_width=body.line_width,
        page_height=body.page_height,
    )
    brf_bytes = text_to_brf_bytes(body.text, config=config)
    return Response(
        content=brf_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": 'attachment; filename="export.brf"',
            "Content-Type": "application/octet-stream",
        },
    )
