"""Tenant isolation utilities for multi-tenancy enforcement.

Provides a TenantContext value object and helpers that read from
``contextvars`` (set by the tenant context middleware) to ensure
every data access is scoped to the authenticated teacher.

Usage in service/repository layer::

    from ailine_runtime.shared.tenant import get_tenant

    ctx = get_tenant()
    ctx.verify_access(resource.teacher_id)  # raises 403 on mismatch

The ``teacher_id`` is injected into ``contextvars`` by
``TenantContextMiddleware`` during request processing. Outside a
request context (e.g. CLI scripts, background workers) callers must
set the context variable explicitly via ``set_tenant_id()``.
"""

from __future__ import annotations

import contextvars
import re

from ..domain.exceptions import (
    InvalidTenantIdError,
    TenantNotFoundError,
    UnauthorizedAccessError,
)

# ---------------------------------------------------------------------------
# Context variable: populated by TenantContextMiddleware
# ---------------------------------------------------------------------------

_tenant_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("ailine_tenant_id", default=None)

# Precompiled patterns for validation.
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_SIMPLE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def validate_teacher_id_format(teacher_id: str) -> str:
    """Validate that *teacher_id* is a well-formed identifier.

    Accepts:
    - Standard UUID format (8-4-4-4-12 hex digits).
    - Simple alphanumeric + hyphen/underscore identifiers up to 128 chars
      (e.g. ``teacher-001``) for backward compatibility with dev fixtures.

    Returns:
        The stripped teacher_id.

    Raises:
        InvalidTenantIdError: If the value is empty, too long, or contains
            characters outside ``[a-zA-Z0-9_-]``.
    """
    tid = teacher_id.strip()
    if not tid:
        raise InvalidTenantIdError("teacher_id must not be empty.")
    if len(tid) > 128:
        raise InvalidTenantIdError("teacher_id exceeds maximum length (128 characters).")
    if _UUID_RE.match(tid):
        return tid
    if _SIMPLE_ID_RE.match(tid):
        return tid
    raise InvalidTenantIdError(
        "teacher_id must be a UUID or contain only alphanumeric characters, hyphens, and underscores."
    )


def set_tenant_id(teacher_id: str) -> contextvars.Token[str | None]:
    """Set the current tenant ID in contextvars.

    Returns a token that can be used to reset the variable
    (e.g. in a ``finally`` block).
    """
    return _tenant_id_var.set(teacher_id)


def clear_tenant_id(token: contextvars.Token[str | None]) -> None:
    """Reset the tenant ID context variable using the given token."""
    _tenant_id_var.reset(token)


def get_current_teacher_id() -> str:
    """Return the current tenant's teacher_id.

    Raises:
        TenantNotFoundError: If no teacher_id is set in the current
            request context (i.e. the middleware did not run or the
            request did not carry authentication).
    """
    tid = _tenant_id_var.get()
    if tid is None:
        raise TenantNotFoundError("Authentication required: no teacher_id in request context.")
    return tid


def try_get_current_teacher_id() -> str | None:
    """Return the current tenant's teacher_id, or None if not set.

    Unlike ``get_current_teacher_id()``, this does not raise. Use it
    in code paths where the tenant context is optional (e.g. listing
    public resources).
    """
    return _tenant_id_var.get()


class TenantContext:
    """Value object representing the authenticated tenant for the current request.

    Provides ``verify_access()`` to enforce that a resource belongs
    to the authenticated teacher, raising 403 on mismatch.
    """

    __slots__ = ("teacher_id",)

    def __init__(self, teacher_id: str) -> None:
        self.teacher_id = teacher_id

    def verify_access(self, resource_teacher_id: str) -> None:
        """Assert that *resource_teacher_id* matches the authenticated tenant.

        Raises:
            UnauthorizedAccessError: If the resource belongs to a different tenant.
        """
        if resource_teacher_id != self.teacher_id:
            raise UnauthorizedAccessError("Access denied: resource belongs to a different tenant.")

    def __repr__(self) -> str:
        return f"TenantContext(teacher_id={self.teacher_id!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TenantContext):
            return self.teacher_id == other.teacher_id
        return NotImplemented


def get_tenant() -> TenantContext:
    """Build a ``TenantContext`` from the current request's contextvars.

    Raises:
        TenantNotFoundError: If no teacher_id is set.
    """
    return TenantContext(teacher_id=get_current_teacher_id())
