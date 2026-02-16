"""Initial schema -- all 11 AiLine tables.

Revision ID: 0001
Revises: None
Create Date: 2026-02-12

Creates: teachers, courses, lessons, materials, chunks,
         pipeline_runs, tutor_agents, tutor_sessions,
         curriculum_objectives, run_events, accessibility_profiles.

The pgvector extension and embedding column on chunks are created
conditionally (only when running against PostgreSQL).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- pgvector extension (Postgres only) --------------------------------
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- teachers ----------------------------------------------------------
    op.create_table(
        "teachers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), unique=True, nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("locale", sa.String(10), server_default="pt-BR"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # --- courses -----------------------------------------------------------
    op.create_table(
        "courses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "teacher_id",
            sa.String(36),
            sa.ForeignKey("teachers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("grade", sa.String(50), nullable=False),
        sa.Column("standard", sa.String(20), server_default="BNCC"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # --- lessons (composite FK for tenant safety, ADR-053) -----------------
    op.create_table(
        "lessons",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("teacher_id", sa.String(36), nullable=False),
        sa.Column("course_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("plan_json", sa.JSON, server_default="{}"),
        sa.Column("student_plan_json", sa.JSON, server_default="{}"),
        sa.Column("accessibility_json", sa.JSON, server_default="{}"),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["teacher_id", "course_id"],
            ["courses.teacher_id", "courses.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_lessons_teacher_course", "lessons", ["teacher_id", "course_id"])

    # --- materials ---------------------------------------------------------
    op.create_table(
        "materials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "teacher_id",
            sa.String(36),
            sa.ForeignKey("teachers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tags", sa.JSON, server_default="[]"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # --- chunks ------------------------------------------------------------
    op.create_table(
        "chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "material_id",
            sa.String(36),
            sa.ForeignKey("materials.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata_json", sa.JSON, server_default="{}"),
    )
    # pgvector embedding column (Postgres only)
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE chunks ADD COLUMN embedding vector(1536)")
        op.execute(
            "CREATE INDEX ix_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops)"
        )

    # --- pipeline_runs -----------------------------------------------------
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "teacher_id",
            sa.String(36),
            sa.ForeignKey("teachers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "lesson_id",
            sa.String(36),
            sa.ForeignKey("lessons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("input_json", sa.JSON, server_default="{}"),
        sa.Column("output_json", sa.JSON, server_default="{}"),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # --- tutor_agents ------------------------------------------------------
    op.create_table(
        "tutor_agents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "teacher_id",
            sa.String(36),
            sa.ForeignKey("teachers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("grade", sa.String(50), nullable=False),
        sa.Column("config_json", sa.JSON, server_default="{}"),
        sa.Column("persona_json", sa.JSON, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # --- tutor_sessions ----------------------------------------------------
    op.create_table(
        "tutor_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tutor_id",
            sa.String(36),
            sa.ForeignKey("tutor_agents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("messages_json", sa.JSON, server_default="[]"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # --- curriculum_objectives ---------------------------------------------
    op.create_table(
        "curriculum_objectives",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(80), unique=True, nullable=False),
        sa.Column("system", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("grade", sa.String(50), nullable=False),
        sa.Column("domain", sa.String(200), server_default=""),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("keywords", sa.JSON, server_default="[]"),
    )
    op.create_index(
        "ix_curriculum_system_grade", "curriculum_objectives", ["system", "grade"]
    )

    # --- run_events --------------------------------------------------------
    op.create_table(
        "run_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(36),
            sa.ForeignKey("pipeline_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("stage", sa.String(30), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("data_json", sa.JSON, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    # --- accessibility_profiles --------------------------------------------
    op.create_table(
        "accessibility_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "teacher_id",
            sa.String(36),
            sa.ForeignKey("teachers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("needs_json", sa.JSON, server_default="{}"),
        sa.Column("supports_json", sa.JSON, server_default="{}"),
        sa.Column("ui_prefs_json", sa.JSON, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    op.drop_table("accessibility_profiles")
    op.drop_table("run_events")
    op.drop_table("curriculum_objectives")
    op.drop_table("tutor_sessions")
    op.drop_table("tutor_agents")
    op.drop_table("pipeline_runs")
    op.drop_table("chunks")
    op.drop_table("materials")
    op.drop_table("lessons")
    op.drop_table("courses")
    op.drop_table("teachers")
