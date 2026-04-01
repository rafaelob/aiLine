"""No-op: UniqueConstraints moved to migration 0002 (where composite FKs are created).

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-27

Originally this migration added UniqueConstraint("teacher_id", "id") on
lessons, materials, and tutor_agents. These constraints are now created
in 0002 (before the composite FK creation) to satisfy PostgreSQL 16's
requirement. This migration is kept as a no-op to preserve the revision chain.
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "0006"
down_revision: str = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass  # UniqueConstraints now created in 0002


def downgrade() -> None:
    pass  # UniqueConstraints now dropped in 0002 downgrade
