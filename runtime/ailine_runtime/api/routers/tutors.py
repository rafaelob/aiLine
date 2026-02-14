"""Tutors API router — tutor agent CRUD + chat.

Chat uses the LangGraph tutor workflow (via ailine_agents) for validated
structured output, tool access, and RAG integration.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...app.authz import require_authenticated, require_tenant_access
from ...shared.sanitize import sanitize_prompt
from ...tutoring.builder import create_tutor_agent, load_tutor_spec
from ...tutoring.session import create_session, load_session, save_session

router = APIRouter()


class TutorCreateIn(BaseModel):
    teacher_id: str
    subject: str
    grade: str
    standard: str = "BNCC"
    style: Literal["socratic", "coach", "direct", "explainer"] = "socratic"
    tone: str = "calmo, paciente, encorajador"
    student_profile: dict[str, Any]
    class_accessibility_profile: dict[str, Any] | None = None
    material_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    auto_persona: bool = False


def _resolve_teacher_id_required() -> str:
    """Resolve teacher_id from JWT context (mandatory).

    Raises 401 if no authenticated teacher context is available.
    """
    return require_authenticated()


@router.post("")
async def tutors_create(body: TutorCreateIn, request: Request):
    teacher_id = _resolve_teacher_id_required()

    settings = request.app.state.settings
    spec = await create_tutor_agent(
        cfg=settings,
        teacher_id=teacher_id,
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

    # Centralized tenant verification (ADR-060)
    require_tenant_access(spec.teacher_id, action="read", resource="tutor")

    return spec.model_dump()


class TutorSessionCreateOut(BaseModel):
    session_id: str


@router.post("/{tutor_id}/sessions")
async def tutor_create_session(tutor_id: str):
    spec = load_tutor_spec(tutor_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Tutor not found")

    # Centralized tenant verification (ADR-060)
    require_tenant_access(spec.teacher_id, action="create", resource="tutor session")

    s = create_session(tutor_id)
    save_session(s)
    return TutorSessionCreateOut(session_id=s.session_id)


class TutorChatIn(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=4000)


@router.post("/{tutor_id}/chat")
async def tutor_chat(tutor_id: str, body: TutorChatIn, request: Request):
    container = request.app.state.container

    # --- Input sanitization ---
    body.message = sanitize_prompt(body.message, max_length=4000)
    if not body.message:
        raise HTTPException(status_code=422, detail="message must not be empty after sanitization")

    spec = load_tutor_spec(tutor_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Tutor not found")

    # Centralized tenant verification (ADR-060)
    require_tenant_access(spec.teacher_id, action="chat", resource="tutor")

    session = load_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.tutor_id != tutor_id:
        raise HTTPException(status_code=400, detail="Session does not belong to this tutor")

    # Update session with user message
    session.append("user", body.message)

    # Build AgentDeps from container
    from ailine_agents.deps import AgentDepsFactory
    from ailine_agents.workflows.tutor_workflow import build_tutor_workflow, run_tutor_turn

    deps = AgentDepsFactory.from_container(
        container,
        teacher_id=spec.teacher_id,
        subject=spec.subject,
    )

    workflow = build_tutor_workflow(deps)

    # Build history from session messages
    history = [{"role": m.role, "content": m.content} for m in session.messages[:-1]]

    result = await run_tutor_turn(
        workflow=workflow,
        tutor_id=tutor_id,
        session_id=session.session_id,
        user_message=body.message,
        history=history,
        spec=spec.model_dump(),
    )

    # Persist assistant response in session
    validated = result.get("validated_output") or {}
    answer = validated.get("answer_markdown", "")
    session.append("assistant", answer)
    save_session(session)

    return {
        "validated": validated,
        "session_id": session.session_id,
        "error": result.get("error"),
    }
