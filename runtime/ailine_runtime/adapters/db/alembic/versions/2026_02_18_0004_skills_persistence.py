"""Skills DB persistence: skills, skill_versions, skill_ratings, teacher_skill_sets.

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-18

Adds 4 new tables for the Skills system (F-175):
- skills: main skill definitions with pgvector embedding
- skill_versions: version history
- skill_ratings: teacher ratings (1-5)
- teacher_skill_sets: named skill presets per teacher
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- skills ----------------------------------------------------------------
    op.create_table(
        "skills",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("instructions_md", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), server_default="{}"),
        sa.Column("license", sa.String(255), server_default=""),
        sa.Column("compatibility", sa.String(500), server_default=""),
        sa.Column("allowed_tools", sa.Text(), server_default=""),
        sa.Column(
            "teacher_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "forked_from_id",
            sa.String(36),
            sa.ForeignKey("skills.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("avg_rating", sa.Float(), server_default="0.0"),
        sa.Column("rating_count", sa.Integer(), server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_skills_teacher", "skills", ["teacher_id"])
    op.create_index("ix_skills_is_active", "skills", ["is_active"])

    # pgvector embedding column (Postgres only, same pattern as chunks in 0001)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE skills ADD COLUMN embedding vector(1536)")
        op.execute(
            "CREATE INDEX ix_skills_embedding ON skills "
            "USING hnsw (embedding vector_cosine_ops) "
            "WITH (m = 16, ef_construction = 128)"
        )

    # --- skill_versions --------------------------------------------------------
    op.create_table(
        "skill_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "skill_id",
            sa.String(36),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("instructions_md", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), server_default="{}"),
        sa.Column("change_summary", sa.Text(), server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_skill_versions_skill", "skill_versions", ["skill_id"])
    op.create_unique_constraint(
        "uq_skill_version", "skill_versions", ["skill_id", "version"]
    )

    # --- skill_ratings ---------------------------------------------------------
    op.create_table(
        "skill_ratings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "skill_id",
            sa.String(36),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_skill_ratings_skill", "skill_ratings", ["skill_id"])
    op.create_unique_constraint(
        "uq_skill_user_rating", "skill_ratings", ["skill_id", "user_id"]
    )

    # --- teacher_skill_sets ----------------------------------------------------
    op.create_table(
        "teacher_skill_sets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "teacher_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("skill_slugs_json", sa.JSON(), server_default="[]"),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_teacher_skill_sets_teacher", "teacher_skill_sets", ["teacher_id"]
    )
    op.create_unique_constraint(
        "uq_teacher_skillset_name", "teacher_skill_sets", ["teacher_id", "name"]
    )


def downgrade() -> None:
    op.drop_table("teacher_skill_sets")
    op.drop_table("skill_ratings")
    op.drop_table("skill_versions")
    # Drop embedding index first (Postgres only)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_skills_embedding")
    op.drop_table("skills")
