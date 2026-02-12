"""SQLAlchemy-based Unit of Work implementation.

Provides transactional boundaries per ADR-052: each LangGraph node
opens and closes its own UoW; sessions are never held across LLM calls.

Conforms to the ``domain.ports.db.UnitOfWork`` protocol.
"""

from __future__ import annotations

from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .repositories import (
    CourseRepository,
    LessonRepository,
    MaterialRepository,
    PipelineRunRepository,
    TeacherRepository,
)


class SqlAlchemyUnitOfWork:
    """Async context manager wrapping a single SQLAlchemy session.

    Usage::

        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            teacher = await uow.teachers.get("some-id")
            await uow.teachers.add(new_teacher)
            await uow.commit()

    Repositories are lazily initialised on first access so there is
    zero overhead if a particular aggregate is not touched.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        # Lazy repository caches
        self._teachers: TeacherRepository | None = None
        self._courses: CourseRepository | None = None
        self._lessons: LessonRepository | None = None
        self._materials: MaterialRepository | None = None
        self._pipeline_runs: PipelineRunRepository | None = None

    # -- Context manager ----------------------------------------------------

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if self._session is not None:
            if exc_type is not None:
                await self._session.rollback()
            await self._session.close()
            self._session = None
        # Reset lazy caches so they cannot be reused after close
        self._teachers = None
        self._courses = None
        self._lessons = None
        self._materials = None
        self._pipeline_runs = None

    # -- Transaction controls -----------------------------------------------

    async def commit(self) -> None:
        """Commit the current transaction."""
        assert self._session is not None, "UoW not entered"
        await self._session.commit()

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        assert self._session is not None, "UoW not entered"
        await self._session.rollback()

    # -- Raw session access (escape hatch) -----------------------------------

    @property
    def session(self) -> AsyncSession:
        """Direct session access for advanced queries."""
        assert self._session is not None, "UoW not entered"
        return self._session

    # -- Lazy repository accessors -------------------------------------------

    @property
    def teachers(self) -> TeacherRepository:
        """Teacher aggregate repository."""
        if self._teachers is None:
            self._teachers = TeacherRepository(self.session)
        return self._teachers

    @property
    def courses(self) -> CourseRepository:
        """Course aggregate repository."""
        if self._courses is None:
            self._courses = CourseRepository(self.session)
        return self._courses

    @property
    def lessons(self) -> LessonRepository:
        """Lesson aggregate repository."""
        if self._lessons is None:
            self._lessons = LessonRepository(self.session)
        return self._lessons

    @property
    def materials(self) -> MaterialRepository:
        """Material aggregate repository."""
        if self._materials is None:
            self._materials = MaterialRepository(self.session)
        return self._materials

    @property
    def pipeline_runs(self) -> PipelineRunRepository:
        """PipelineRun aggregate repository."""
        if self._pipeline_runs is None:
            self._pipeline_runs = PipelineRunRepository(self.session)
        return self._pipeline_runs
