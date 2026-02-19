"""Tests for UserRepository implementations (InMemoryUserRepository).

Covers:
- create: stores user and makes it findable by email and id
- get_by_email: returns None for missing, correct UserRow for existing
- get_by_id: returns None for missing, correct UserRow for existing
- seed_sync: synchronous insert for startup seeding
- has_email: synchronous existence check
"""

from __future__ import annotations

import pytest

from ailine_runtime.adapters.db.models import UserRow
from ailine_runtime.adapters.db.user_repository import InMemoryUserRepository


@pytest.fixture()
def repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


def _make_user(
    email: str = "test@example.com",
    display_name: str = "Test User",
    role: str = "teacher",
    **kwargs: object,
) -> UserRow:
    from uuid_utils import uuid7

    defaults = {
        "id": str(uuid7()),
        "locale": "en",
        "avatar_url": "",
        "accessibility_profile": "",
        "is_active": True,
        "hashed_password": "",
    }
    defaults.update(kwargs)
    return UserRow(email=email, display_name=display_name, role=role, **defaults)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


async def test_create_stores_user(repo: InMemoryUserRepository) -> None:
    user = _make_user()
    await repo.create(user)
    found = await repo.get_by_email("test@example.com")
    assert found is not None
    assert found.email == "test@example.com"
    assert found.display_name == "Test User"


async def test_create_findable_by_id(repo: InMemoryUserRepository) -> None:
    user = _make_user()
    await repo.create(user)
    found = await repo.get_by_id(user.id)
    assert found is not None
    assert found.id == user.id


# ---------------------------------------------------------------------------
# get_by_email
# ---------------------------------------------------------------------------


async def test_get_by_email_returns_none_for_missing(
    repo: InMemoryUserRepository,
) -> None:
    result = await repo.get_by_email("nonexistent@example.com")
    assert result is None


async def test_get_by_email_returns_correct_user(
    repo: InMemoryUserRepository,
) -> None:
    user1 = _make_user(email="a@test.com", display_name="A")
    user2 = _make_user(email="b@test.com", display_name="B")
    await repo.create(user1)
    await repo.create(user2)

    found = await repo.get_by_email("b@test.com")
    assert found is not None
    assert found.display_name == "B"


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


async def test_get_by_id_returns_none_for_missing(
    repo: InMemoryUserRepository,
) -> None:
    result = await repo.get_by_id("nonexistent-id")
    assert result is None


# ---------------------------------------------------------------------------
# seed_sync
# ---------------------------------------------------------------------------


def test_seed_sync_stores_user(repo: InMemoryUserRepository) -> None:
    user = _make_user(email="seed@demo.edu")
    repo.seed_sync(user)
    assert repo.has_email("seed@demo.edu")


def test_seed_sync_findable_by_id(repo: InMemoryUserRepository) -> None:
    user = _make_user(email="seed2@demo.edu")
    repo.seed_sync(user)

    # Verify it's in _by_id too (synchronous access)
    assert user.id in repo._by_id


# ---------------------------------------------------------------------------
# has_email
# ---------------------------------------------------------------------------


def test_has_email_false_for_empty(repo: InMemoryUserRepository) -> None:
    assert not repo.has_email("ghost@example.com")


def test_has_email_true_after_create(repo: InMemoryUserRepository) -> None:
    user = _make_user(email="exists@test.com")
    repo.seed_sync(user)
    assert repo.has_email("exists@test.com")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


async def test_multiple_users_independent(
    repo: InMemoryUserRepository,
) -> None:
    """Multiple users stored independently."""
    for i in range(5):
        await repo.create(_make_user(email=f"user{i}@test.com", display_name=f"User {i}"))

    for i in range(5):
        found = await repo.get_by_email(f"user{i}@test.com")
        assert found is not None
        assert found.display_name == f"User {i}"


async def test_user_row_explicit_id(repo: InMemoryUserRepository) -> None:
    """UserRow with explicit ID is stored and retrievable."""
    user = _make_user(id="explicit-id-001")
    await repo.create(user)
    found = await repo.get_by_id("explicit-id-001")
    assert found is not None
    assert found.id == "explicit-id-001"
