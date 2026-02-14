"""Domain-level exceptions for AiLine.

These exceptions live in the domain layer and carry no HTTP/framework
coupling. The API layer maps them to appropriate HTTP responses via
the error handler middleware.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain exceptions."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TenantNotFoundError(DomainError):
    """Raised when no tenant context is available (not authenticated)."""


class UnauthorizedAccessError(DomainError):
    """Raised when a tenant tries to access a resource they do not own."""


class InvalidTenantIdError(DomainError):
    """Raised when a teacher_id fails format validation."""
