"""Port: database repository and unit-of-work protocols."""

from __future__ import annotations

from typing import Any, Protocol, Self, runtime_checkable


@runtime_checkable
class Repository(Protocol):
    """Generic repository protocol."""

    async def get(self, id: str) -> Any | None: ...
    async def list(self, **filters: Any) -> list[Any]: ...
    async def add(self, entity: Any) -> Any: ...
    async def update(self, entity: Any) -> Any: ...
    async def delete(self, id: str) -> None: ...


@runtime_checkable
class UnitOfWork(Protocol):
    """Async context manager for transactional boundaries."""

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None: ...

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
