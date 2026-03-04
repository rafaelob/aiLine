"""Materials API router."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ...app.authz import require_authenticated
from ...materials.store import add_material, iter_materials

router = APIRouter()


class MaterialIn(BaseModel):
    subject: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)


@router.post("")
async def materials_add(
    body: MaterialIn,
    teacher_id: str = Depends(require_authenticated),
):
    m = add_material(
        teacher_id=teacher_id,
        subject=body.subject,
        title=body.title,
        content=body.content,
        tags=body.tags,
    )
    return asdict(m)


@router.get("")
async def materials_list(
    subject: str | None = None,
    teacher_id: str = Depends(require_authenticated),
):

    return [asdict(m) for m in iter_materials(teacher_id=teacher_id, subject=subject)]
