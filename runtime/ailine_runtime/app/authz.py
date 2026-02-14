"""Centralized authorization policies (ADR-060).

Routes MUST call these instead of ad-hoc inline checks.
All authorization decisions are funneled through this module
so that policy changes propagate uniformly across the codebase.
"""

from __future__ import annotations

from ..domain.exceptions import DomainError
from ..shared.tenant import TenantContext, get_current_teacher_id, get_tenant


class AuthorizationError(Exception):
    """Raised when an authorization check fails.

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
