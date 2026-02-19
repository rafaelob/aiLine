"""Centralized authorization policies (ADR-060).

Routes MUST call these instead of ad-hoc inline checks.
All authorization decisions are funneled through this module
so that policy changes propagate uniformly across the codebase.
"""

from __future__ import annotations

from ..domain.entities.user import UserRole
from ..domain.exceptions import DomainError
from ..shared.tenant import (
    TenantContext,
    get_current_teacher_id,
    get_current_user_role,
    get_tenant,
)


class AuthorizationError(DomainError):
    """Raised when an authorization check fails.

    Extends DomainError so it is caught by the RFC 7807 error handler
    and returns a proper 403 response instead of a generic 500.

    Attributes:
        action: The attempted action (e.g. "read", "write", "delete").
        resource: A human-readable resource description.
    """

    def __init__(self, action: str, resource: str) -> None:
        self.action = action
        self.resource = resource
        super().__init__(f"Not authorized to {action} {resource}")


def require_tenant_access(
    resource_teacher_id: str,
    *,
    action: str = "access",
    resource: str = "resource",
) -> TenantContext:
    """Verify that the current user owns *resource_teacher_id*.

    Raises:
        TenantNotFoundError: If no tenant context is set.
        UnauthorizedAccessError: If the resource belongs to another tenant.

    Returns:
        The ``TenantContext`` for the authenticated teacher.
    """
    ctx = get_tenant()
    ctx.verify_access(resource_teacher_id)
    return ctx


def require_authenticated() -> str:
    """Verify that the current request has an authenticated teacher.

    Raises:
        TenantNotFoundError: If no teacher_id is set in the context.

    Returns:
        The authenticated teacher_id.
    """
    return get_current_teacher_id()


def can_observe() -> bool:
    """Check whether the current user may access observability endpoints.

    For now any authenticated teacher can observe their own data.
    Returns ``False`` instead of raising when no auth context is present.
    """
    try:
        require_authenticated()
        return True
    except DomainError:
        return False


# ---------------------------------------------------------------------------
# Role-based authorization (RBAC)
# ---------------------------------------------------------------------------


def require_role(*allowed_roles: str) -> str:
    """Verify the current user has one of the allowed roles.

    Super admins bypass all role checks.

    Returns:
        The authenticated user's ID (teacher_id / user_id).

    Raises:
        TenantNotFoundError: If no auth context is set.
        AuthorizationError: If the user's role is not in *allowed_roles*.
    """
    teacher_id = require_authenticated()
    role = get_current_user_role()

    # Super admin can do anything
    if role == UserRole.SUPER_ADMIN:
        return teacher_id

    if role not in allowed_roles:
        raise AuthorizationError(
            action="access",
            resource=f"endpoint requiring role(s): {', '.join(allowed_roles)}",
        )
    return teacher_id


def require_admin() -> str:
    """Require super_admin or school_admin role."""
    return require_role(UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN)


def require_teacher_or_admin() -> str:
    """Require teacher, school_admin, or super_admin role."""
    return require_role(
        UserRole.SUPER_ADMIN, UserRole.SCHOOL_ADMIN, UserRole.TEACHER,
    )


def require_any_authenticated_role() -> str:
    """Any authenticated user regardless of role."""
    return require_authenticated()


def can_access_student_data(student_id: str) -> bool:
    """Synchronous check if current user can access a student's data.

    Handles deterministic cases only (super_admin bypass, student self-access).
    For relationship-based access, use ``check_student_access()`` which queries
    the DB for teacher-student and parent-student relationships.
    """
    try:
        user_id = require_authenticated()
        role = get_current_user_role()

        if role == UserRole.SUPER_ADMIN:
            return True
        if role == UserRole.STUDENT:
            return user_id == student_id
        return False
    except Exception:
        return False


async def check_student_access(
    student_id: str,
    session: object,
) -> bool:
    """Async DB-backed check for student data access.

    Queries the teacher_students and parent_students junction tables
    to verify relationship-based access.

    Args:
        student_id: The student whose data is being accessed.
        session: An AsyncSession for querying relationship tables.

    Returns:
        True if the current user is authorized to access the student's data.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from ..adapters.db.models import ParentStudentRow, TeacherStudentRow

    # First check deterministic cases
    if can_access_student_data(student_id):
        return True

    try:
        user_id = require_authenticated()
        role = get_current_user_role()
    except Exception:
        return False

    if not isinstance(session, AsyncSession):
        return False

    if role == UserRole.TEACHER or role == UserRole.SCHOOL_ADMIN:
        stmt = select(TeacherStudentRow).where(
            TeacherStudentRow.teacher_id == user_id,
            TeacherStudentRow.student_id == student_id,
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            return True

    if role == UserRole.PARENT:
        stmt = select(ParentStudentRow).where(
            ParentStudentRow.parent_id == user_id,
            ParentStudentRow.student_id == student_id,
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is not None:
            return True

    return False
