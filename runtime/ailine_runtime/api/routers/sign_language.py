"""Sign language API router -- gesture recognition, supported gestures, and Libras captioning.

Endpoints resolve the ``SignRecognition`` adapter from ``app.state.container``.
When no real model is configured the container falls back to
``FakeSignRecognition``, which keeps the API testable without external models.

WebSocket /ws/libras-caption provides real-time gloss → Portuguese captioning.

MVP scope (ADR-026): 4 basic Libras gestures (oi, obrigado, sim, nao).
Extended scope: 30-gloss captioning with CTC decoding + LLM translation.
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field

from ...accessibility.caption_orchestrator import CaptionOrchestrator
from ...accessibility.gloss_translator import GlossToTextTranslator
from ...api.middleware.tenant_context import _extract_teacher_id_from_jwt
from ...app.authz import require_authenticated

logger = structlog.get_logger(__name__)

router = APIRouter()

# -- File upload size limits ---------------------------------------------------

MAX_SIGN_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB (video/image of gesture)


# -- Response schemas --------------------------------------------------------


class RecognitionResult(BaseModel):
    """Result of a sign language gesture recognition."""

    gesture: str = Field(..., description="Predicted gesture label.")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Prediction confidence (0-1)."
    )
    landmarks: list[Any] = Field(
        default_factory=list,
        description="Detected hand landmarks (empty in placeholder mode).",
    )
    model: str = Field(..., description="Model identifier used for recognition.")
    note: str | None = Field(None, description="Optional note about the recognition.")


class GestureInfo(BaseModel):
    """Description of a single supported gesture."""

    id: str
    name_pt: str
    name_en: str
    name_es: str


class GestureListResponse(BaseModel):
    """List of all gestures supported by the current model."""

    gestures: list[GestureInfo]
    model: str
    note: str


# -- Supported gestures (canonical MVP list, ADR-026) -----------------------

_SUPPORTED_GESTURES: list[GestureInfo] = [
    GestureInfo(
        id="oi",
        name_pt="Oi / Ola",
        name_en="Hello",
        name_es="Hola",
    ),
    GestureInfo(
        id="obrigado",
        name_pt="Obrigado/a",
        name_en="Thank you",
        name_es="Gracias",
    ),
    GestureInfo(
        id="sim",
        name_pt="Sim",
        name_en="Yes",
        name_es="Si",
    ),
    GestureInfo(
        id="nao",
        name_pt="Nao",
        name_en="No",
        name_es="No",
    ),
]


# -- Helper to resolve adapter ----------------------------------------------


def _get_sign_recognizer(request: Request) -> Any:
    """Retrieve the sign recognition adapter from the DI container.

    Raises HTTP 503 if the adapter is not configured.
    """
    container = request.app.state.container
    recognizer = getattr(container, "sign_recognition", None)
    if recognizer is None:
        raise HTTPException(
            status_code=503,
            detail="Sign recognition adapter is not configured.",
        )
    return recognizer


# -- Endpoints ---------------------------------------------------------------


@router.post("/recognize", response_model=RecognitionResult)
async def recognize_sign(
    request: Request,
    file: UploadFile,
) -> RecognitionResult:
    """Recognize a sign language gesture from a video or image upload.

    Accepts video (webm, mp4) or image (png, jpg) files containing a
    hand gesture.  The server-side model extracts MediaPipe hand landmarks
    and classifies the gesture via an MLP.

    For MVP, the fake adapter returns a deterministic result based on
    input size; the real adapter returns "unknown" until a trained model
    is provided.
    """
    require_authenticated()
    recognizer = _get_sign_recognizer(request)
    video_bytes = await file.read()
    if not video_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")
    if len(video_bytes) > MAX_SIGN_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Maximum size: 10MB."
        )

    content_type = file.content_type or "unknown"
    logger.info(
        "sign_language.recognize",
        content_type=content_type,
        size=len(video_bytes),
    )

    result = await recognizer.recognize(video_bytes)
    return RecognitionResult(**result)


@router.get("/gestures", response_model=GestureListResponse)
async def list_gestures() -> GestureListResponse:
    """List all gestures supported by the current sign language model.

    MVP scope: 4 basic Libras gestures (ADR-026).
    """
    return GestureListResponse(
        gestures=_SUPPORTED_GESTURES,
        model="mediapipe-mlp",
        note="MVP: 4 basic Libras gestures (oi, obrigado, sim, nao)",
    )


# -- WebSocket: Libras gloss captioning -------------------------------------


@router.websocket("/ws/libras-caption")
async def libras_caption_ws(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time Libras gloss → Portuguese captioning.

    Authentication: pass JWT as ``?token=<jwt>`` query parameter.
    The token is verified before accepting the connection.

    Protocol (client → server):
      {"type": "gloss_partial", "glosses": ["EU", "GOSTAR"], "confidence": 0.75, "ts": 1234}
      {"type": "gloss_final",   "glosses": ["EU", "GOSTAR"], "confidence": 0.95, "ts": 1234}

    Protocol (server → client):
      {"type": "caption_draft_delta", "text": "Eu gosto...", "glosses": [...], "confidence": 0.75}
      {"type": "caption_final_delta", "text": "Eu gosto da escola.", "full_text": "...", "glosses": [...]}
      {"type": "error", "detail": "..."}
    """
    # Authenticate via query parameter token before accepting the connection.
    token = websocket.query_params.get("token", "")
    if token:
        teacher_id, _error = _extract_teacher_id_from_jwt(token)
        if not teacher_id:
            await websocket.close(code=4001, reason="Authentication failed")
            return
    else:
        # Allow unauthenticated WebSocket only in dev mode for backward compat
        import os

        if os.getenv("AILINE_DEV_MODE", "").lower() not in ("true", "1", "yes"):
            await websocket.close(
                code=4001, reason="Authentication required: pass ?token=<jwt>"
            )
            return
        teacher_id = None

    await websocket.accept()

    # Resolve LLM from container
    container = websocket.app.state.container
    llm = getattr(container, "llm", None)
    if llm is None:
        await websocket.send_json({"type": "error", "detail": "LLM not configured"})
        await websocket.close(code=1011)
        return

    translator = GlossToTextTranslator(llm=llm)

    async def emit_message(msg: dict[str, Any]) -> None:
        await websocket.send_json(msg)

    orchestrator = CaptionOrchestrator(
        translator=translator,
        emit=emit_message,
    )

    logger.info("libras_caption.session_start")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
                continue

            msg_type = message.get("type")
            if msg_type not in ("gloss_partial", "gloss_final"):
                await websocket.send_json(
                    {
                        "type": "error",
                        "detail": f"Unknown message type: {msg_type}",
                    }
                )
                continue

            await orchestrator.handle_message(message)

    except WebSocketDisconnect:
        logger.info("libras_caption.session_end")
    except Exception:
        logger.exception("libras_caption.error")
    finally:
        orchestrator.reset()
