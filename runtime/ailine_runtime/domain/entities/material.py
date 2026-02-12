"""Material-related domain entities.

Pure Pydantic models representing teacher-uploaded educational materials
and their chunked representations for vector search.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Material(BaseModel):
    """A single educational material uploaded by a teacher."""

    material_id: str
    teacher_id: str
    subject: str
    title: str
    tags: list[str] = Field(default_factory=list)
    content: str
    created_at: str


class MaterialChunk(BaseModel):
    """A chunk of a material, ready for embedding and vector search."""

    chunk_id: str
    material_id: str
    chunk_index: int
    content: str
    embedding: list[float] | None = None
    metadata: dict = Field(default_factory=dict)
