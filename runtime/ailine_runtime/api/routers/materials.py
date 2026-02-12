"""Materials API router."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...materials.store import add_material, iter_materials

router = APIRouter()


class MaterialIn(BaseModel):
    teacher_id: str
    subject: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)


@router.post("")
async def materials_add(body: MaterialIn):
    m = add_material(
        teacher_id=body.teacher_id,
        subject=body.subject,
        title=body.title,
        content=body.content,
        tags=body.tags,
    )
    return m.__dict__


@router.get("")
async def materials_list(teacher_id: str | None = None, subject: str | None = None):
    return [m.__dict__ for m in iter_materials(teacher_id=teacher_id, subject=subject)]
