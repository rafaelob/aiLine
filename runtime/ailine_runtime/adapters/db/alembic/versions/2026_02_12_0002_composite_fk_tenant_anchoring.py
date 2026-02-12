"""Composite FK tenant anchoring for TutorSession, PipelineRun, Chunk.

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-12

ADR-053: Adds composite foreign keys to enforce tenant safety at the DB level:
- chunks: (teacher_id, material_id) -> materials(teacher_id, id)
- pipeline_runs: (teacher_id, lesson_id) -> lessons(teacher_id, id)
- tutor_sessions: (teacher_id, tutor_id) -> tutor_agents(teacher_id, id)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- chunks: add teacher_id + composite FK ---
    op.add_column("chunks", sa.Column("teacher_id", sa.String(36), nullable=False))
    # Drop old simple FK on material_id
    op.drop_constraint("fk_chunks_material_id", "chunks", type_="foreignkey")
    op.create_foreign_key(
        "fk_chunks_teacher_material",
        "chunks",
        "materials",
        ["teacher_id", "material_id"],
        ["teacher_id", "id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_chunks_teacher_material", "chunks", ["teacher_id", "material_id"])

    # --- pipeline_runs: replace simple lesson FK with composite ---
    # Drop old simple FK on lesson_id
    op.drop_constraint("fk_pipeline_runs_lesson_id", "pipeline_runs", type_="foreignkey")
    op.create_foreign_key(
        "fk_pipeline_runs_teacher_lesson",
        "pipeline_runs",
        "lessons",
        ["teacher_id", "lesson_id"],
        ["teacher_id", "id"],
        ondelete="SET NULL",
    )

    # --- tutor_sessions: add teacher_id + composite FK ---
    op.add_column("tutor_sessions", sa.Column("teacher_id", sa.String(36), nullable=False))
    # Drop old simple FK on tutor_id
    op.drop_constraint("fk_tutor_sessions_tutor_id", "tutor_sessions", type_="foreignkey")
    op.create_foreign_key(
        "fk_tutor_sessions_teacher_tutor",
        "tutor_sessions",
        "tutor_agents",
        ["teacher_id", "tutor_id"],
        ["teacher_id", "id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_tutor_sessions_teacher_tutor",
        "tutor_sessions",
        ["teacher_id", "tutor_id"],
    )


def downgrade() -> None:
    # --- tutor_sessions: revert to simple FK ---
    op.drop_index("ix_tutor_sessions_teacher_tutor", "tutor_sessions")
    op.drop_constraint("fk_tutor_sessions_teacher_tutor", "tutor_sessions", type_="foreignkey")
    op.create_foreign_key(
        "fk_tutor_sessions_tutor_id",
        "tutor_sessions",
        "tutor_agents",
        ["tutor_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_column("tutor_sessions", "teacher_id")

    # --- pipeline_runs: revert to simple lesson FK ---
    op.drop_constraint("fk_pipeline_runs_teacher_lesson", "pipeline_runs", type_="foreignkey")
    op.create_foreign_key(
        "fk_pipeline_runs_lesson_id",
        "pipeline_runs",
        "lessons",
        ["lesson_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- chunks: revert to simple FK ---
    op.drop_index("ix_chunks_teacher_material", "chunks")
    op.drop_constraint("fk_chunks_teacher_material", "chunks", type_="foreignkey")
    op.create_foreign_key(
        "fk_chunks_material_id",
        "chunks",
        "materials",
        ["material_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_column("chunks", "teacher_id")
