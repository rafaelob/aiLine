"""User and organization domain entities for RBAC system."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class UserRole(StrEnum):
    """User roles in the RBAC system."""

    SUPER_ADMIN = "super_admin"
    SCHOOL_ADMIN = "school_admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


class Organization(BaseModel):
    """A school or educational institution."""

    id: str
    name: str
    slug: str
    type: str = Field(default="school", description="school|course|district")
    address: str = ""
    contact_email: str = ""
    created_at: str = ""


class User(BaseModel):
    """A user in the system (any role)."""

    id: str
    email: str
    display_name: str
    role: UserRole
    org_id: str | None = None
    locale: str = "en"
    avatar_url: str = ""
    accessibility_profile: str = ""
    is_active: bool = True
    created_at: str = ""


class StudentProfile(BaseModel):
    """Extended profile for student users."""

    user_id: str
    grade: str = ""
    accessibility_needs: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    accommodations: list[str] = Field(default_factory=list)
    parent_ids: list[str] = Field(default_factory=list)
    teacher_ids: list[str] = Field(default_factory=list)
