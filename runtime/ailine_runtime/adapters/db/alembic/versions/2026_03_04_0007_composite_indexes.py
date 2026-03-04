"""Add composite indexes for common query patterns.

Revision ID: 0007
Revises: 0006
Create Date: 2026-03-04
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_materials_teacher_subject", "materials", ["teacher_id", "subject"])
    op.create_index(
        "ix_pipeline_runs_teacher_status",
        "pipeline_runs",
        ["teacher_id", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_pipeline_runs_teacher_status", table_name="pipeline_runs")
    op.drop_index("ix_materials_teacher_subject", table_name="materials")
