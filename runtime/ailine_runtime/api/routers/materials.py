"""Materials API router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...materials.store import add_material, iter_materials
from ...shared.sanitize import validate_teacher_id
from ...shared.tenant import try_get_current_teacher_id

router = APIRouter()


class MaterialIn(BaseModel):
    teacher_id: str
    subject: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)


def _resolve_teacher_id_required(body_teacher_id: str) -> str:
    """Resolve teacher_id: middleware context takes precedence over body."""
    ctx_teacher_id = try_get_current_teacher_id()
    if ctx_teacher_id:
        return ctx_teacher_id
    try:
        return validate_teacher_id(body_teacher_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("")
async def materials_add(body: MaterialIn):
    teacher_id = _resolve_teacher_id_required(body.teacher_id)

    m = add_material(
        teacher_id=teacher_id,
        subject=body.subject,
        title=body.title,
        content=body.content,
        tags=body.tags,
    )
    return m.__dict__


@router.get("")
async def materials_list(teacher_id: str | None = None, subject: str | None = None):
    # If tenant context is available, use it to scope the listing
    ctx_teacher_id = try_get_current_teacher_id()
    effective_teacher_id = ctx_teacher_id or teacher_id

    return [m.__dict__ for m in iter_materials(teacher_id=effective_teacher_id, subject=subject)]
