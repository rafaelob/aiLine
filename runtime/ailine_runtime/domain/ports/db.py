"""Port: database repository and unit-of-work protocols."""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class Repository(Protocol[T]):
    """Generic repository protocol.

    Type parameter T represents the entity type managed by this repository.
    """

    async def get(self, id: str) -> T | None: ...
    async def list(self, **filters: str) -> list[T]: ...
    async def add(self, entity: T) -> T: ...
    async def update(self, entity: T) -> T: ...
    async def delete(self, id: str) -> None: ...


@runtime_checkable
class UnitOfWork(Protocol):
    """Async context manager for transactional boundaries."""

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
