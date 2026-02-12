"""Tutors API router — tutor agent CRUD + chat."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...tutoring.builder import create_tutor_agent, load_tutor_spec
from ...tutoring.session import create_session, load_session, save_session, tutor_chat_turn

router = APIRouter()


class TutorCreateIn(BaseModel):
    teacher_id: str
    subject: str
    grade: str
    standard: str = "BNCC"
    style: str = "socratic"
    tone: str = "calmo, paciente, encorajador"
    student_profile: dict[str, Any]
    class_accessibility_profile: dict[str, Any] | None = None
    material_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    auto_persona: bool = False


@router.post("")
async def tutors_create(body: TutorCreateIn, request: Request):
    settings = request.app.state.settings
    spec = await create_tutor_agent(
        cfg=settings,
        teacher_id=body.teacher_id,
        subject=body.subject,
        grade=body.grade,
        standard=body.standard,
        style=body.style,
        tone=body.tone,
        student_profile=body.student_profile,
        class_accessibility_profile=body.class_accessibility_profile,
        material_ids=body.material_ids,
        tags=body.tags,
        auto_persona=body.auto_persona,
    )
    return spec.model_dump()


@router.get("/{tutor_id}")
async def tutors_get(tutor_id: str):
    spec = load_tutor_spec(tutor_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Tutor not found")
    return spec.model_dump()


class TutorSessionCreateOut(BaseModel):
    session_id: str


@router.post("/{tutor_id}/sessions")
async def tutor_create_session(tutor_id: str):
    spec = load_tutor_spec(tutor_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Tutor not found")
    s = create_session(tutor_id)
    save_session(s)
    return TutorSessionCreateOut(session_id=s.session_id)


class TutorChatIn(BaseModel):
    session_id: str
    message: str


@router.post("/{tutor_id}/chat")
async def tutor_chat(tutor_id: str, body: TutorChatIn, request: Request):
    settings = request.app.state.settings
    from ...tools.registry import build_tool_registry

    registry = build_tool_registry()

    session = load_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.tutor_id != tutor_id:
        raise HTTPException(status_code=400, detail="Session does not belong to this tutor")

    result = await tutor_chat_turn(
        cfg=settings,
        registry=registry,
        tutor_id=tutor_id,
        session=session,
        user_message=body.message,
    )
    return result
