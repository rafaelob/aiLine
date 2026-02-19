"""Tests for the RBAC authorization module (authz.py, ADR-060).

Covers:
- require_authenticated: success and unauthenticated error
- require_role: per-role checks, super_admin bypass, denied roles
- require_admin: super_admin and school_admin allowed, others denied
- require_teacher_or_admin: teacher/school_admin/super_admin allowed
- require_any_authenticated_role: any role succeeds
- require_tenant_access: same tenant, cross-tenant, super_admin bypass
- can_observe: authenticated vs unauthenticated
- can_access_student_data: full permission matrix per role
- AuthorizationError attributes
"""

from __future__ import annotations

import pytest

from ailine_runtime.app.authz import (
    AuthorizationError,
    can_access_student_data,
    can_observe,
    require_admin,
    require_any_authenticated_role,
    require_authenticated,
    require_role,
    require_teacher_or_admin,
    require_tenant_access,
)
from ailine_runtime.domain.entities.user import UserRole
from ailine_runtime.domain.exceptions import (
    TenantNotFoundError,
    UnauthorizedAccessError,
)
from ailine_runtime.shared.tenant import (
    clear_org_id,
    clear_tenant_id,
    clear_user_role,
    set_org_id,
    set_tenant_id,
    set_user_role,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_tenant_context():
    """Ensure tenant context is clean before and after each test."""
    # Set and immediately clear to get a clean state
    tid_token = set_tenant_id("__cleanup__")
    clear_tenant_id(tid_token)
    role_token = set_user_role("__cleanup__")
    clear_user_role(role_token)
    org_token = set_org_id("__cleanup__")
    clear_org_id(org_token)
    yield
    # Cleanup is handled by the tokens above being out of scope;
    # but we also want to reset any tokens set during tests.
    # Since contextvars are task-scoped, the next test will start clean.


class _TenantContextHelper:
    """Context manager to set and clear tenant context cleanly."""

    def __init__(
        self,
        teacher_id: str,
        role: str | None = None,
        org_id: str | None = None,
    ) -> None:
        self._teacher_id = teacher_id
        self._role = role
        self._org_id = org_id
        self._tid_token = None
        self._role_token = None
        self._org_token = None

    def __enter__(self):
        self._tid_token = set_tenant_id(self._teacher_id)
        if self._role is not None:
            self._role_token = set_user_role(self._role)
        if self._org_id is not None:
            self._org_token = set_org_id(self._org_id)
        return self

    def __exit__(self, *args):
        if self._tid_token is not None:
            clear_tenant_id(self._tid_token)
        if self._role_token is not None:
            clear_user_role(self._role_token)
        if self._org_token is not None:
            clear_org_id(self._org_token)


# ---------------------------------------------------------------------------
# AuthorizationError
# ---------------------------------------------------------------------------


class TestAuthorizationError:
    """Tests for the AuthorizationError exception class."""

    def test_error_has_action_and_resource(self) -> None:
        err = AuthorizationError(action="delete", resource="course")
        assert err.action == "delete"
        assert err.resource == "course"

    def test_error_message_format(self) -> None:
        err = AuthorizationError(action="write", resource="lesson plan")
        assert str(err) == "Not authorized to write lesson plan"

    def test_error_is_exception(self) -> None:
        err = AuthorizationError(action="read", resource="data")
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# require_authenticated
# ---------------------------------------------------------------------------


class TestRequireAuthenticated:
    """Tests for require_authenticated()."""

    def test_returns_teacher_id_when_set(self) -> None:
        with _TenantContextHelper("teacher-001"):
            result = require_authenticated()
            assert result == "teacher-001"

    def test_raises_when_no_tenant(self) -> None:
        with pytest.raises(TenantNotFoundError):
            require_authenticated()

    def test_returns_uuid_teacher_id(self) -> None:
        uid = "550e8400-e29b-41d4-a716-446655440000"
        with _TenantContextHelper(uid):
            assert require_authenticated() == uid


# ---------------------------------------------------------------------------
# require_role
# ---------------------------------------------------------------------------


class TestRequireRole:
    """Tests for require_role() with various role combinations."""

    def test_super_admin_bypasses_any_role_check(self) -> None:
        """Super admin should be allowed regardless of allowed_roles."""
        with _TenantContextHelper("admin-001", role=UserRole.SUPER_ADMIN):
            result = require_role(UserRole.TEACHER)
            assert result == "admin-001"

    def test_super_admin_bypasses_empty_role_list(self) -> None:
        """Super admin should pass even with no allowed roles specified."""
        with _TenantContextHelper("admin-001", role=UserRole.SUPER_ADMIN):
            # Even an empty set of allowed roles is bypassed by super_admin
            result = require_role()
            assert result == "admin-001"

    def test_matching_role_succeeds(self) -> None:
        with _TenantContextHelper("teacher-001", role=UserRole.TEACHER):
            result = require_role(UserRole.TEACHER)
            assert result == "teacher-001"

    def test_multiple_allowed_roles_match(self) -> None:
        with _TenantContextHelper("teacher-001", role=UserRole.TEACHER):
            result = require_role(UserRole.TEACHER, UserRole.SCHOOL_ADMIN)
            assert result == "teacher-001"

    def test_non_matching_role_raises(self) -> None:
        with _TenantContextHelper("student-001", role=UserRole.STUDENT):
            with pytest.raises(AuthorizationError) as exc_info:
                require_role(UserRole.TEACHER)
            assert exc_info.value.action == "access"
            assert "teacher" in exc_info.value.resource.lower()

    def test_parent_denied_teacher_role(self) -> None:
        with _TenantContextHelper("parent-001", role=UserRole.PARENT), pytest.raises(
            AuthorizationError
        ):
            require_role(UserRole.TEACHER)

    def test_school_admin_in_allowed_roles(self) -> None:
        with _TenantContextHelper("admin-001", role=UserRole.SCHOOL_ADMIN):
            result = require_role(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
            assert result == "admin-001"

    def test_student_in_allowed_roles(self) -> None:
        with _TenantContextHelper("student-001", role=UserRole.STUDENT):
            result = require_role(UserRole.STUDENT, UserRole.PARENT)
            assert result == "student-001"

    def test_raises_when_unauthenticated(self) -> None:
        with pytest.raises(TenantNotFoundError):
            require_role(UserRole.TEACHER)


# ---------------------------------------------------------------------------
# require_admin
# ---------------------------------------------------------------------------


class TestRequireAdmin:
    """Tests for require_admin() -- super_admin or school_admin only."""

    def test_super_admin_allowed(self) -> None:
        with _TenantContextHelper("sa-001", role=UserRole.SUPER_ADMIN):
            assert require_admin() == "sa-001"

    def test_school_admin_allowed(self) -> None:
        with _TenantContextHelper("school-001", role=UserRole.SCHOOL_ADMIN):
            assert require_admin() == "school-001"

    def test_teacher_denied(self) -> None:
        with _TenantContextHelper("teacher-001", role=UserRole.TEACHER), pytest.raises(
            AuthorizationError
        ):
            require_admin()

    def test_student_denied(self) -> None:
        with _TenantContextHelper("student-001", role=UserRole.STUDENT), pytest.raises(
            AuthorizationError
        ):
            require_admin()

    def test_parent_denied(self) -> None:
        with _TenantContextHelper("parent-001", role=UserRole.PARENT), pytest.raises(
            AuthorizationError
        ):
            require_admin()


# ---------------------------------------------------------------------------
# require_teacher_or_admin
# ---------------------------------------------------------------------------


class TestRequireTeacherOrAdmin:
    """Tests for require_teacher_or_admin() -- teacher, school_admin, or super_admin."""

    def test_super_admin_allowed(self) -> None:
        with _TenantContextHelper("sa-001", role=UserRole.SUPER_ADMIN):
            assert require_teacher_or_admin() == "sa-001"

    def test_school_admin_allowed(self) -> None:
        with _TenantContextHelper("school-001", role=UserRole.SCHOOL_ADMIN):
            assert require_teacher_or_admin() == "school-001"

    def test_teacher_allowed(self) -> None:
        with _TenantContextHelper("teacher-001", role=UserRole.TEACHER):
            assert require_teacher_or_admin() == "teacher-001"

    def test_student_denied(self) -> None:
        with _TenantContextHelper("student-001", role=UserRole.STUDENT), pytest.raises(
            AuthorizationError
        ):
            require_teacher_or_admin()

    def test_parent_denied(self) -> None:
        with _TenantContextHelper("parent-001", role=UserRole.PARENT), pytest.raises(
            AuthorizationError
        ):
            require_teacher_or_admin()


# ---------------------------------------------------------------------------
# require_any_authenticated_role
# ---------------------------------------------------------------------------


class TestRequireAnyAuthenticatedRole:
    """Tests for require_any_authenticated_role() -- any role succeeds."""

    @pytest.mark.parametrize(
        "role",
        [
            UserRole.SUPER_ADMIN,
            UserRole.SCHOOL_ADMIN,
            UserRole.TEACHER,
            UserRole.STUDENT,
            UserRole.PARENT,
        ],
    )
    def test_all_roles_allowed(self, role: str) -> None:
        with _TenantContextHelper(f"user-{role}", role=role):
            result = require_any_authenticated_role()
            assert result == f"user-{role}"

    def test_unauthenticated_denied(self) -> None:
        with pytest.raises(TenantNotFoundError):
            require_any_authenticated_role()


# ---------------------------------------------------------------------------
# require_tenant_access
# ---------------------------------------------------------------------------


class TestRequireTenantAccess:
    """Tests for require_tenant_access() -- tenant isolation enforcement."""

    def test_same_tenant_allowed(self) -> None:
        with _TenantContextHelper("teacher-001", role=UserRole.TEACHER):
            ctx = require_tenant_access("teacher-001")
            assert ctx.teacher_id == "teacher-001"
            assert ctx.role == UserRole.TEACHER

    def test_cross_tenant_denied(self) -> None:
        with _TenantContextHelper("teacher-001", role=UserRole.TEACHER), pytest.raises(
            UnauthorizedAccessError
        ):
            require_tenant_access("teacher-002")

    def test_super_admin_can_access_any_tenant(self) -> None:
        with _TenantContextHelper("admin-001", role=UserRole.SUPER_ADMIN):
            ctx = require_tenant_access("teacher-999")
            assert ctx.teacher_id == "admin-001"

    def test_returns_tenant_context_with_org(self) -> None:
        with _TenantContextHelper("t-001", role=UserRole.TEACHER, org_id="org-A"):
            ctx = require_tenant_access("t-001")
            assert ctx.org_id == "org-A"

    def test_custom_action_and_resource(self) -> None:
        with _TenantContextHelper("teacher-001", role=UserRole.TEACHER), pytest.raises(
            UnauthorizedAccessError
        ):
            require_tenant_access("teacher-002", action="delete", resource="lesson")

    def test_unauthenticated_raises(self) -> None:
        with pytest.raises(TenantNotFoundError):
            require_tenant_access("teacher-001")


# ---------------------------------------------------------------------------
# can_observe
# ---------------------------------------------------------------------------


class TestCanObserve:
    """Tests for can_observe() -- observability access check."""

    def test_returns_true_when_authenticated(self) -> None:
        with _TenantContextHelper("teacher-001"):
            assert can_observe() is True

    def test_returns_false_when_not_authenticated(self) -> None:
        assert can_observe() is False


# ---------------------------------------------------------------------------
# can_access_student_data -- full RBAC permission matrix
# ---------------------------------------------------------------------------


class TestCanAccessStudentData:
    """Tests for can_access_student_data() -- student data access permission matrix."""

    def test_super_admin_can_access_any_student(self) -> None:
        with _TenantContextHelper("admin-001", role=UserRole.SUPER_ADMIN):
            assert can_access_student_data("student-001") is True
            assert can_access_student_data("student-999") is True

    def test_student_can_access_own_data(self) -> None:
        with _TenantContextHelper("student-001", role=UserRole.STUDENT):
            assert can_access_student_data("student-001") is True

    def test_student_cannot_access_other_student(self) -> None:
        with _TenantContextHelper("student-001", role=UserRole.STUDENT):
            assert can_access_student_data("student-002") is False

    def test_teacher_denied_without_db_check(self) -> None:
        """Teacher denied at policy layer — service must do DB relationship check."""
        with _TenantContextHelper("teacher-001", role=UserRole.TEACHER):
            assert can_access_student_data("student-001") is False

    def test_parent_denied_without_db_check(self) -> None:
        """Parent denied at policy layer — service must do DB relationship check."""
        with _TenantContextHelper("parent-001", role=UserRole.PARENT):
            assert can_access_student_data("student-001") is False

    def test_school_admin_denied_without_db_check(self) -> None:
        """School admin denied at policy layer — service must do DB relationship check."""
        with _TenantContextHelper("school-001", role=UserRole.SCHOOL_ADMIN):
            assert can_access_student_data("student-001") is False

    def test_unauthenticated_returns_false(self) -> None:
        assert can_access_student_data("student-001") is False

    @pytest.mark.parametrize(
        ("role", "student_id", "user_id", "expected"),
        [
            (UserRole.SUPER_ADMIN, "s-100", "sa-001", True),
            (UserRole.STUDENT, "s-100", "s-100", True),
            (UserRole.STUDENT, "s-200", "s-100", False),
            (UserRole.TEACHER, "s-100", "t-001", False),
            (UserRole.PARENT, "s-100", "p-001", False),
            (UserRole.SCHOOL_ADMIN, "s-100", "a-001", False),
        ],
    )
    def test_permission_matrix(
        self, role: str, student_id: str, user_id: str, expected: bool
    ) -> None:
        with _TenantContextHelper(user_id, role=role):
            assert can_access_student_data(student_id) is expected
