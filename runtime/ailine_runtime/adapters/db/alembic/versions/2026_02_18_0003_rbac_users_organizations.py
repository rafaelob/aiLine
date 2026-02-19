"""RBAC: users, organizations, student profiles, and relationship tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-18

Adds the core RBAC schema:
- organizations: schools/institutions
- users: unified user table with role column
- student_profiles: extended data for student users
- teacher_students: many-to-many teacher <-> student
- parent_students: many-to-many parent <-> student

The existing 'teachers' table is preserved for backward compatibility.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- organizations ---
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("type", sa.String(20), server_default="school"),
        sa.Column("address", sa.Text(), server_default=""),
        sa.Column("contact_email", sa.String(320), server_default=""),
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

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), unique=True, nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="teacher"),
        sa.Column(
            "org_id",
            sa.String(36),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("locale", sa.String(10), server_default="en"),
        sa.Column("avatar_url", sa.String(500), server_default=""),
        sa.Column("accessibility_profile", sa.String(50), server_default=""),
        sa.Column("hashed_password", sa.String(256), server_default=""),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
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
    op.create_index("ix_users_org_id", "users", ["org_id"])

    # --- student_profiles ---
    op.create_table(
        "student_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("grade", sa.String(50), server_default=""),
        sa.Column("accessibility_needs", sa.JSON(), server_default="[]"),
        sa.Column("strengths", sa.JSON(), server_default="[]"),
        sa.Column("accommodations", sa.JSON(), server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # --- teacher_students ---
    op.create_table(
        "teacher_students",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "teacher_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_teacher_students_teacher", "teacher_students", ["teacher_id"])
    op.create_index("ix_teacher_students_student", "teacher_students", ["student_id"])

    # --- parent_students ---
    op.create_table(
        "parent_students",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "parent_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_parent_students_parent", "parent_students", ["parent_id"])
    op.create_index("ix_parent_students_student", "parent_students", ["student_id"])


def downgrade() -> None:
    op.drop_table("parent_students")
    op.drop_table("teacher_students")
    op.drop_table("student_profiles")
    op.drop_index("ix_users_org_id", "users")
    op.drop_table("users")
    op.drop_table("organizations")
