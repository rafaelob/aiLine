"""Fix skills.slug: drop global unique, add composite unique (teacher_id, slug).

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-19

The initial skills migration (0004) created a global unique constraint on
skills.slug, which prevents different teachers from forking the same slug.
The ORM model declares UniqueConstraint("teacher_id", "slug") -- this migration
aligns the DB with the ORM.

Also adds a partial unique index for system skills (teacher_id IS NULL) so
built-in skill slugs remain globally unique.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # Drop the auto-generated global unique constraint on slug
        op.execute(
            "ALTER TABLE skills DROP CONSTRAINT IF EXISTS skills_slug_key"
        )
        # Also drop index-based unique if Alembic created one instead
        op.execute("DROP INDEX IF EXISTS ix_skills_slug")

        # Add composite unique constraint matching the ORM
        op.create_unique_constraint(
            "uq_skills_teacher_slug", "skills", ["teacher_id", "slug"]
        )

        # Partial unique index for system skills (teacher_id IS NULL)
        # ensures built-in skill slugs are globally unique.
        op.execute(
            "CREATE UNIQUE INDEX ix_skills_system_slug_unique "
            "ON skills (slug) WHERE teacher_id IS NULL"
        )
    else:
        # SQLite: the ORM's table_args already define the composite unique
        # via SQLAlchemy's create_all. No ALTER TABLE needed for test DBs.
        pass


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_skills_system_slug_unique")
        op.execute(
            "ALTER TABLE skills DROP CONSTRAINT IF EXISTS uq_skills_teacher_slug"
        )
        # Restore global unique on slug (original state from 0004)
        op.create_unique_constraint("skills_slug_key", "skills", ["slug"])
