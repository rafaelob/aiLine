"""Tests for domain entities: UserRole, User, Organization, StudentProfile.

Covers:
- UserRole enum: all 5 roles, StrEnum behavior, string comparison
- User model: required/optional fields, defaults, role validation
- Organization model: fields, defaults, type options
- StudentProfile model: fields, list defaults, relationships
- Cross-entity relationships and consistency
"""

from __future__ import annotations

import pytest

from ailine_runtime.domain.entities.user import (
    Organization,
    StudentProfile,
    User,
    UserRole,
)

# ---------------------------------------------------------------------------
# UserRole enum
# ---------------------------------------------------------------------------


class TestUserRole:
    """Tests for the UserRole StrEnum."""

    def test_has_five_roles(self) -> None:
        assert len(UserRole) == 5

    @pytest.mark.parametrize(
        ("member", "value"),
        [
            (UserRole.SUPER_ADMIN, "super_admin"),
            (UserRole.SCHOOL_ADMIN, "school_admin"),
            (UserRole.TEACHER, "teacher"),
            (UserRole.STUDENT, "student"),
            (UserRole.PARENT, "parent"),
        ],
    )
    def test_role_values(self, member: UserRole, value: str) -> None:
        assert member.value == value

    def test_is_str_enum(self) -> None:
        """UserRole values should be directly usable as strings."""
        assert str(UserRole.TEACHER) == "teacher"
        assert UserRole.SUPER_ADMIN == "super_admin"

    def test_string_comparison(self) -> None:
        """Role values should be comparable to plain strings."""
        assert UserRole.TEACHER == "teacher"
        assert UserRole.STUDENT != "teacher"

    def test_membership_check(self) -> None:
        """Can check if a string value is a valid role."""
        valid = {r.value for r in UserRole}
        assert "teacher" in valid
        assert "admin" not in valid
        assert "super_admin" in valid

    def test_invalid_role_raises(self) -> None:
        with pytest.raises(ValueError):
            UserRole("moderator")

    def test_role_from_string(self) -> None:
        role = UserRole("teacher")
        assert role == UserRole.TEACHER
        assert role is UserRole.TEACHER


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


class TestUserModel:
    """Tests for the User Pydantic model."""

    def test_required_fields(self) -> None:
        user = User(
            id="u-001",
            email="teacher@school.edu",
            display_name="Ms. Johnson",
            role=UserRole.TEACHER,
        )
        assert user.id == "u-001"
        assert user.email == "teacher@school.edu"
        assert user.display_name == "Ms. Johnson"
        assert user.role == UserRole.TEACHER

    def test_optional_defaults(self) -> None:
        user = User(
            id="u-002",
            email="test@test.com",
            display_name="Test",
            role=UserRole.STUDENT,
        )
        assert user.org_id is None
        assert user.locale == "en"
        assert user.avatar_url == ""
        assert user.accessibility_profile == ""
        assert user.is_active is True
        assert user.created_at == ""

    def test_all_fields_populated(self) -> None:
        user = User(
            id="u-003",
            email="admin@district.edu",
            display_name="Admin User",
            role=UserRole.SUPER_ADMIN,
            org_id="org-district-01",
            locale="pt-BR",
            avatar_url="https://example.com/avatar.png",
            accessibility_profile="high_contrast",
            is_active=True,
            created_at="2026-02-18T10:00:00Z",
        )
        assert user.org_id == "org-district-01"
        assert user.locale == "pt-BR"
        assert user.avatar_url == "https://example.com/avatar.png"
        assert user.accessibility_profile == "high_contrast"

    def test_inactive_user(self) -> None:
        user = User(
            id="u-004",
            email="inactive@test.com",
            display_name="Inactive",
            role=UserRole.TEACHER,
            is_active=False,
        )
        assert user.is_active is False

    @pytest.mark.parametrize("role", list(UserRole))
    def test_all_roles_accepted(self, role: UserRole) -> None:
        user = User(
            id=f"u-{role.value}",
            email=f"{role.value}@test.com",
            display_name=f"Test {role.value}",
            role=role,
        )
        assert user.role == role

    def test_user_serialization(self) -> None:
        user = User(
            id="u-005",
            email="serial@test.com",
            display_name="Serial User",
            role=UserRole.PARENT,
            org_id="org-001",
        )
        data = user.model_dump()
        assert data["id"] == "u-005"
        assert data["role"] == "parent"
        assert data["org_id"] == "org-001"
        assert data["is_active"] is True

    def test_user_from_dict(self) -> None:
        data = {
            "id": "u-006",
            "email": "fromdict@test.com",
            "display_name": "From Dict",
            "role": "school_admin",
        }
        user = User.model_validate(data)
        assert user.role == UserRole.SCHOOL_ADMIN


# ---------------------------------------------------------------------------
# Organization model
# ---------------------------------------------------------------------------


class TestOrganizationModel:
    """Tests for the Organization Pydantic model."""

    def test_required_fields(self) -> None:
        org = Organization(
            id="org-001",
            name="Green Valley School",
            slug="green-valley-school",
        )
        assert org.id == "org-001"
        assert org.name == "Green Valley School"
        assert org.slug == "green-valley-school"

    def test_optional_defaults(self) -> None:
        org = Organization(
            id="org-002",
            name="Test Org",
            slug="test-org",
        )
        assert org.type == "school"
        assert org.address == ""
        assert org.contact_email == ""
        assert org.created_at == ""

    def test_all_fields_populated(self) -> None:
        org = Organization(
            id="org-003",
            name="District Central",
            slug="district-central",
            type="district",
            address="123 Main St, Anytown, USA",
            contact_email="admin@district.edu",
            created_at="2026-01-15T00:00:00Z",
        )
        assert org.type == "district"
        assert org.address == "123 Main St, Anytown, USA"
        assert org.contact_email == "admin@district.edu"

    @pytest.mark.parametrize("org_type", ["school", "course", "district"])
    def test_valid_org_types(self, org_type: str) -> None:
        org = Organization(
            id=f"org-{org_type}",
            name=f"Test {org_type}",
            slug=f"test-{org_type}",
            type=org_type,
        )
        assert org.type == org_type

    def test_serialization(self) -> None:
        org = Organization(
            id="org-004",
            name="Test School",
            slug="test-school",
            type="school",
        )
        data = org.model_dump()
        assert data["id"] == "org-004"
        assert data["type"] == "school"
        assert data["slug"] == "test-school"


# ---------------------------------------------------------------------------
# StudentProfile model
# ---------------------------------------------------------------------------


class TestStudentProfileModel:
    """Tests for the StudentProfile Pydantic model."""

    def test_required_user_id(self) -> None:
        profile = StudentProfile(user_id="s-001")
        assert profile.user_id == "s-001"

    def test_optional_defaults(self) -> None:
        profile = StudentProfile(user_id="s-002")
        assert profile.grade == ""
        assert profile.accessibility_needs == []
        assert profile.strengths == []
        assert profile.accommodations == []
        assert profile.parent_ids == []
        assert profile.teacher_ids == []

    def test_all_fields_populated(self) -> None:
        profile = StudentProfile(
            user_id="s-003",
            grade="6th",
            accessibility_needs=["adhd", "dyslexia"],
            strengths=["visual_learning", "creativity"],
            accommodations=["extra_time", "text_to_speech"],
            parent_ids=["p-001", "p-002"],
            teacher_ids=["t-001"],
        )
        assert profile.grade == "6th"
        assert len(profile.accessibility_needs) == 2
        assert "adhd" in profile.accessibility_needs
        assert "dyslexia" in profile.accessibility_needs
        assert len(profile.strengths) == 2
        assert len(profile.accommodations) == 2
        assert len(profile.parent_ids) == 2
        assert profile.teacher_ids == ["t-001"]

    def test_list_fields_are_independent(self) -> None:
        """Verify list defaults are not shared across instances."""
        p1 = StudentProfile(user_id="s-a")
        p2 = StudentProfile(user_id="s-b")
        p1.accessibility_needs.append("visual")
        assert p2.accessibility_needs == []

    def test_serialization(self) -> None:
        profile = StudentProfile(
            user_id="s-004",
            grade="8th",
            accessibility_needs=["hearing_impairment"],
            parent_ids=["p-003"],
        )
        data = profile.model_dump()
        assert data["user_id"] == "s-004"
        assert data["grade"] == "8th"
        assert data["accessibility_needs"] == ["hearing_impairment"]
        assert data["parent_ids"] == ["p-003"]
        assert data["strengths"] == []
        assert data["teacher_ids"] == []

    def test_from_dict(self) -> None:
        data = {
            "user_id": "s-005",
            "grade": "4th",
            "accessibility_needs": ["asd"],
            "accommodations": ["visual_schedule"],
        }
        profile = StudentProfile.model_validate(data)
        assert profile.user_id == "s-005"
        assert profile.accessibility_needs == ["asd"]
        assert profile.accommodations == ["visual_schedule"]
        assert profile.strengths == []


# ---------------------------------------------------------------------------
# Cross-entity relationship tests
# ---------------------------------------------------------------------------


class TestCrossEntityRelationships:
    """Tests for consistency across domain entities."""

    def test_user_role_matches_student_profile(self) -> None:
        """A StudentProfile should reference a User with role=STUDENT."""
        user = User(
            id="s-001",
            email="alex@school.edu",
            display_name="Alex",
            role=UserRole.STUDENT,
            org_id="org-001",
        )
        profile = StudentProfile(
            user_id=user.id,
            grade="5th",
            accessibility_needs=["adhd"],
            teacher_ids=["t-001"],
        )
        assert profile.user_id == user.id
        assert user.role == UserRole.STUDENT

    def test_user_org_matches_organization(self) -> None:
        """A User's org_id should reference an Organization."""
        org = Organization(
            id="org-001",
            name="Green Valley",
            slug="green-valley",
        )
        user = User(
            id="t-001",
            email="teacher@greenvalley.edu",
            display_name="Teacher",
            role=UserRole.TEACHER,
            org_id=org.id,
        )
        assert user.org_id == org.id

    def test_parent_student_relationship(self) -> None:
        """Parent IDs in StudentProfile should reference Users with role=PARENT."""
        parent = User(
            id="p-001",
            email="parent@home.com",
            display_name="Parent",
            role=UserRole.PARENT,
        )
        student_profile = StudentProfile(
            user_id="s-001",
            parent_ids=[parent.id],
        )
        assert parent.id in student_profile.parent_ids
        assert parent.role == UserRole.PARENT

    def test_teacher_student_relationship(self) -> None:
        """Teacher IDs in StudentProfile should reference Users with role=TEACHER."""
        teacher = User(
            id="t-001",
            email="teacher@school.edu",
            display_name="Teacher",
            role=UserRole.TEACHER,
        )
        profile = StudentProfile(
            user_id="s-001",
            teacher_ids=[teacher.id],
        )
        assert teacher.id in profile.teacher_ids
