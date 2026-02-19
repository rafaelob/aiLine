"""TTS API router -- dedicated text-to-speech endpoints.

Provides voice discovery and synthesis via the TTS adapter resolved
from ``app.state.container``. Falls back to FakeTTS when no real
adapter is configured.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ...app.authz import require_teacher_or_admin

logger = structlog.get_logger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class TTSSynthesizeRequest(BaseModel):
    """Request body for text-to-speech synthesis."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to synthesize into speech.",
    )
    voice_id: str | None = Field(
        None,
        description="Voice ID. When omitted, uses the adapter's default voice.",
    )
    language: str = Field(
        "en",
        description="BCP-47 language code (e.g. 'en', 'pt-BR').",
    )
    speed: float = Field(
        1.0,
        ge=0.25,
        le=4.0,
        description="Playback speed multiplier.",
    )


class VoiceInfoResponse(BaseModel):
    """Public representation of a TTS voice."""

    id: str
    name: str
    language: str
    gender: str
    preview_url: str
    labels: dict[str, str]


class VoiceListResponse(BaseModel):
    """Response for the voice listing endpoint."""

    voices: list[VoiceInfoResponse]
    total: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_tts(request: Request) -> Any:
    """Resolve the TTS adapter from the DI container."""
    container = request.app.state.container
    tts = getattr(container, "tts", None)
    if tts is None:
        raise HTTPException(
            status_code=503,
            detail="TTS adapter is not configured.",
        )
    return tts


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/synthesize")
async def synthesize_speech(
    request: Request,
    body: TTSSynthesizeRequest,
    _user_id: str = Depends(require_teacher_or_admin),
) -> Response:
    """Synthesize text into audio.

    Returns raw audio bytes (audio/mpeg for ElevenLabs, audio/wav for fake).
    """
    tts = _get_tts(request)

    logger.info(
        "tts.synthesize",
        voice_id=body.voice_id,
        language=body.language,
        speed=body.speed,
        text_length=len(body.text),
    )

    audio_bytes = await tts.synthesize(
        body.text, locale=body.language, speed=body.speed
    )

    # Detect content type from audio header (WAV starts with RIFF).
    if audio_bytes[:4] == b"RIFF":
        media_type = "audio/wav"
        filename = "speech.wav"
    else:
        media_type = "audio/mpeg"
        filename = "speech.mp3"

    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.get("/voices", response_model=VoiceListResponse)
async def list_voices(
    request: Request,
    language: str | None = None,
    _user_id: str = Depends(require_teacher_or_admin),
) -> VoiceListResponse:
    """List available TTS voices, optionally filtered by language."""
    tts = _get_tts(request)

    logger.info("tts.list_voices", language=language)
    voices = await tts.list_voices(language=language)

    return VoiceListResponse(
        voices=[
            VoiceInfoResponse(
                id=v.id,
                name=v.name,
                language=v.language,
                gender=v.gender,
                preview_url=v.preview_url,
                labels=v.labels,
            )
            for v in voices
        ],
        total=len(voices),
    )


@router.get("/voices/{voice_id}", response_model=VoiceInfoResponse)
async def get_voice(
    request: Request,
    voice_id: str,
    _user_id: str = Depends(require_teacher_or_admin),
) -> VoiceInfoResponse:
    """Get details for a specific voice by ID."""
    tts = _get_tts(request)

    logger.info("tts.get_voice", voice_id=voice_id)
    voice = await tts.get_voice(voice_id)

    if voice is None:
        raise HTTPException(
            status_code=404,
            detail=f"Voice '{voice_id}' not found.",
        )

    return VoiceInfoResponse(
        id=voice.id,
        name=voice.name,
        language=voice.language,
        gender=voice.gender,
        preview_url=voice.preview_url,
        labels=voice.labels,
    )
