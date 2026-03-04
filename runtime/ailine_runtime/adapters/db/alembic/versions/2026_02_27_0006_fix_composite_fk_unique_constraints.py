"""Add UniqueConstraint(teacher_id, id) on parent tables for composite FKs.

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-27

PostgreSQL 16 rejects composite FK creation when the referenced columns
lack a matching unique constraint. This migration adds
UniqueConstraint("teacher_id", "id") on courses, lessons, materials,
and tutor_agents — the four parent tables referenced by composite FKs
in ADR-053 (chunks, pipeline_runs, tutor_sessions, lessons).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tables that need UniqueConstraint("teacher_id", "id") for composite FK targets
_TABLES = [
    ("courses", "uq_courses_teacher_id"),
    ("lessons", "uq_lessons_teacher_id"),
    ("materials", "uq_materials_teacher_id"),
    ("tutor_agents", "uq_tutor_agents_teacher_id"),
]


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        for table, constraint_name in _TABLES:
            op.create_unique_constraint(
                constraint_name, table, ["teacher_id", "id"]
            )
    # SQLite: constraints are defined in ORM's create_all; no ALTER needed.


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        for table, constraint_name in reversed(_TABLES):
            op.drop_constraint(constraint_name, table, type_="unique")
