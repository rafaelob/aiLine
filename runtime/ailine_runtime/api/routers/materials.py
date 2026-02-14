"""Materials API router."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ...app.authz import require_authenticated
from ...materials.store import add_material, iter_materials

router = APIRouter()


class MaterialIn(BaseModel):
    teacher_id: str
    subject: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)


def _resolve_teacher_id_required() -> str:
    """Resolve teacher_id from JWT context (mandatory).

    Raises 401 if no authenticated teacher context is available.
    """
    return require_authenticated()


@router.post("")
async def materials_add(body: MaterialIn):
    teacher_id = _resolve_teacher_id_required()

    m = add_material(
        teacher_id=teacher_id,
        subject=body.subject,
        title=body.title,
        content=body.content,
        tags=body.tags,
    )
    return asdict(m)


@router.get("")
async def materials_list(subject: str | None = None):
    # Mandatory auth: always scope queries to the authenticated teacher (ADR-060)
    teacher_id = require_authenticated()

    return [asdict(m) for m in iter_materials(teacher_id=teacher_id, subject=subject)]
