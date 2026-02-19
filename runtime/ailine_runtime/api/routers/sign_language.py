"""Sign language API router -- gesture recognition, international sign language registry, and captioning.

Endpoints resolve the ``SignRecognition`` adapter from ``app.state.container``.
When no real model is configured the container falls back to
``FakeSignRecognition``, which keeps the API testable without external models.

WebSocket /ws/libras-caption provides real-time gloss -> spoken-language captioning.

MVP scope (ADR-026): 4 basic Libras gestures (oi, obrigado, sim, nao).
Extended scope: 8 international sign languages with 8 common gestures each,
30-gloss captioning with CTC decoding + LLM translation.
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field

from ...accessibility.caption_orchestrator import CaptionOrchestrator
from ...accessibility.gloss_translator import GlossToTextTranslator
from ...accessibility.sign_language_registry import (
    COMMON_GESTURES,
    SignLanguageCode,
    SignLanguageInfo,
    get_sign_language,
    get_sign_language_for_locale,
    list_all_sign_languages,
)
from ...api.middleware.tenant_context import extract_teacher_id_from_jwt
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


class SignLanguageGestureItem(BaseModel):
    """A single gesture in a sign language."""

    id: str
    name: str
    gloss: str


class SignLanguageGesturesResponse(BaseModel):
    """List of common gestures for a sign language."""

    sign_language: str
    sign_language_name: str
    gestures: list[SignLanguageGestureItem]
    total: int


class SignLanguageListResponse(BaseModel):
    """List of all supported sign languages."""

    languages: list[SignLanguageInfo]
    total: int


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


# -- International sign language endpoints ------------------------------------


@router.get("/languages", response_model=SignLanguageListResponse)
async def list_sign_languages() -> SignLanguageListResponse:
    """List all supported sign languages.

    Returns metadata for all 8 sign languages supported by the platform:
    ASL, BSL, LGP, DGS, LSF, LSE, Libras, ISL.
    """
    languages = list_all_sign_languages()
    return SignLanguageListResponse(languages=languages, total=len(languages))


@router.get("/languages/{code}", response_model=SignLanguageInfo)
async def get_sign_language_info(code: str) -> SignLanguageInfo:
    """Get detailed information about a specific sign language.

    Args:
        code: Sign language code (e.g., asl, bsl, libras, dgs, lsf, lse, lgp, isl).
    """
    info = get_sign_language(code)
    if info is None:
        valid = ", ".join(c.value for c in SignLanguageCode)
        raise HTTPException(
            status_code=404,
            detail=f"Sign language '{code}' not found. Valid codes: {valid}",
        )
    return info


@router.get(
    "/languages/{code}/gestures",
    response_model=SignLanguageGesturesResponse,
)
async def get_sign_language_gestures(code: str) -> SignLanguageGesturesResponse:
    """Get common gestures for a specific sign language.

    Returns 8 basic gestures (hello, thank you, yes, no, please, sorry, help, understand)
    in the requested sign language.
    """
    info = get_sign_language(code)
    if info is None:
        valid = ", ".join(c.value for c in SignLanguageCode)
        raise HTTPException(
            status_code=404,
            detail=f"Sign language '{code}' not found. Valid codes: {valid}",
        )

    raw_gestures = COMMON_GESTURES.get(info.code, [])
    gestures = [
        SignLanguageGestureItem(
            id=g["id"],
            name=g["name"],
            gloss=g["gloss"],
        )
        for g in raw_gestures
    ]
    return SignLanguageGesturesResponse(
        sign_language=info.code.value,
        sign_language_name=info.name,
        gestures=gestures,
        total=len(gestures),
    )


@router.get("/for-locale/{locale}", response_model=SignLanguageInfo)
async def get_sign_language_for_locale_endpoint(locale: str) -> SignLanguageInfo:
    """Get the recommended sign language for a given locale.

    Locale examples: en, en-US, en-GB, pt-BR, de, fr, es, en-IE.
    Falls back to ASL if the locale is not recognized.
    """
    return get_sign_language_for_locale(locale)


# -- Existing endpoints (backward compatible) ---------------------------------


@router.post("/recognize", response_model=RecognitionResult)
async def recognize_sign(
    request: Request,
    file: UploadFile,
    _teacher_id: str = Depends(require_authenticated),
) -> RecognitionResult:
    """Recognize a sign language gesture from a video or image upload.

    Accepts video (webm, mp4) or image (png, jpg) files containing a
    hand gesture.  The server-side model extracts MediaPipe hand landmarks
    and classifies the gesture via an MLP.

    For MVP, the fake adapter returns a deterministic result based on
    input size; the real adapter returns "unknown" until a trained model
    is provided.
    """
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
async def list_gestures(
    _teacher_id: str = Depends(require_authenticated),
) -> GestureListResponse:
    """List all gestures supported by the current sign language model.

    MVP scope: 4 basic Libras gestures (ADR-026).
    """
    return GestureListResponse(
        gestures=_SUPPORTED_GESTURES,
        model="mediapipe-mlp",
        note="MVP: 4 basic Libras gestures (oi, obrigado, sim, nao)",
    )


# -- WebSocket: sign language gloss captioning --------------------------------


@router.websocket("/ws/libras-caption")
async def libras_caption_ws(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time sign language gloss -> spoken-language captioning.

    Authentication: pass JWT as ``?token=<jwt>`` query parameter.
    The token is verified before accepting the connection.

    Optional: pass ``?lang=<code>`` to set the sign language (default: libras).

    Protocol (client -> server):
      {"type": "gloss_partial", "glosses": ["EU", "GOSTAR"], "confidence": 0.75, "ts": 1234}
      {"type": "gloss_final",   "glosses": ["EU", "GOSTAR"], "confidence": 0.95, "ts": 1234}

    Protocol (server -> client):
      {"type": "caption_draft_delta", "text": "Eu gosto...", "glosses": [...], "confidence": 0.75}
      {"type": "caption_final_delta", "text": "Eu gosto da escola.", "full_text": "...", "glosses": [...]}
      {"type": "error", "detail": "..."}
    """
    # Authenticate via query parameter token before accepting the connection.
    token = websocket.query_params.get("token", "")
    if token:
        teacher_id, _error = extract_teacher_id_from_jwt(token)
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

    # Resolve sign language from query parameter (default: Libras)
    lang_param = websocket.query_params.get("lang", "libras")
    try:
        sign_language = SignLanguageCode(lang_param.lower())
    except ValueError:
        sign_language = SignLanguageCode.LIBRAS

    translator = GlossToTextTranslator(llm=llm, sign_language=sign_language)

    async def emit_message(msg: dict[str, Any]) -> None:
        await websocket.send_json(msg)

    orchestrator = CaptionOrchestrator(
        translator=translator,
        emit=emit_message,
    )

    logger.info(
        "sign_caption.session_start",
        sign_language=sign_language.value,
    )

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
        logger.info(
            "sign_caption.session_end",
            sign_language=sign_language.value,
        )
    except Exception:
        logger.exception("sign_caption.error")
    finally:
        orchestrator.reset()
