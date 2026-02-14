# Sprint 0002 — Database Layer

**Status:** completed | **Date:** 2026-02-12
**Goal:** SQLAlchemy 2.x async ORM models, Alembic migrations, multi-DB support
(Postgres+pgvector primary, SQLite fallback), Docker Compose with pgvector+Redis,
i18n data files.

---

## Verified Library Versions

| Library | Version | Source |
|---------|---------|--------|
| SQLAlchemy | 2.0.46 | pypi.org |
| Alembic | 1.18.4 | pypi.org |
| asyncpg | 0.31.0 | pypi.org |
| aiosqlite | 0.21.0 | pypi.org |
| pgvector-python | 0.4.2 | pypi.org |
| uuid-utils | 0.14.0 | pypi.org |

---

## Architecture Decisions

- **UUID v7 for all PKs**: Time-ordered (better B-tree locality than UUID v4),
  sortable, no sequence contention. **CRITICAL: `uuid.uuid7()` is Python 3.14+,
  NOT Python 3.13.** Must use `uuid-utils` package as a hard (non-optional)
  dependency. Use a compatibility wrapper (see S2-001 implementation patterns)
  that tries stdlib first and falls back to `uuid_utils.uuid7`. This ensures
  zero-effort migration when the project upgrades to Python 3.14.
- **JSONB for flexible fields**: `accessibility_pack`, `metadata`, `export_data`
  columns use JSONB. Essential for adaptive content -- no migration fatigue for
  schema evolution. Indexed with GIN for key lookups. **Use JSONB + Pydantic
  TypeDecorator pattern** for strict roundtrip serialization (see S2-001
  implementation patterns).
- **State machine for pipeline stages**: `status` column with CHECK constraint on
  enum values. Uses the existing Python StrEnum `RunStage` (planner, validate,
  refine, executor, done, failed) from `domain/entities/plan.py`. Transitions
  enforced in application layer (Repository method).
- **Multi-tenancy via `teacher_id` FK**: Column-level filtering on plans,
  materials, tutor sessions. Simple and sufficient for hackathon scope (not
  schema-level RLS separation).
- **ADR-012: App-level tenancy with TenantContext dependency**: Derive tenant
  identity from the authenticated user's auth context (never from request body).
  Enforce via a FastAPI `Depends(get_tenant_ctx)` that injects `TenantContext`
  into every route. **Use `TeacherId` NewType wrapper for type safety** (see
  S2-003 implementation patterns). The repository layer requires `TeacherId` as
  a mandatory parameter on all write and query methods. **`teacher_id` must NEVER
  appear in any request body schema.** Integration tests must verify cross-tenant
  isolation using dedicated `teacher_a` / `teacher_b` fixtures.
- **Multi-DB strategy**: Primary target is Postgres 17 with pgvector extension.
  SQLite via aiosqlite serves as a zero-infrastructure fallback for local dev
  without Docker. Vector column operations are conditional (skipped on SQLite).
- **ORM mapping strategy**: SQLAlchemy 2.0 `Mapped[]` / `mapped_column()`
  declarative style. ORM models are separate from domain entities; repositories
  translate between them. Domain entities remain pure Pydantic with zero ORM
  coupling.
- **Async UoW pattern**: `async_sessionmaker` with `expire_on_commit=False`.
  Connection pool configured with `pool_pre_ping=True` for stale connection
  detection. Repository accessors are cached on the UoW instance (see S2-003
  implementation patterns). Safe commit/rollback in `__aexit__`.

---

## Stories

### S2-001: SQLAlchemy ORM Models (11 tables)

**Description:** Create async SQLAlchemy 2.0 models mapping to all domain
entities. These are ORM table representations -- not Pydantic domain models.
Each model maps 1:1 to a Postgres table. Domain entity <-> ORM model translation
is done in the repository layer.

**Files:**
- `runtime/ailine_runtime/adapters/db/models.py` (all table models)
- `runtime/ailine_runtime/adapters/db/__init__.py` (package init)
- `runtime/ailine_runtime/adapters/db/base.py` (DeclarativeBase + uuid7 wrapper)
- `runtime/ailine_runtime/adapters/db/types.py` (PydanticJSONB TypeDecorator)

**Acceptance Criteria:**
- [ ] All 11 tables defined with proper relationships (ForeignKey + relationship())
- [ ] UUID v7 primary keys on all tables via `new_uuid7()` compatibility wrapper
- [ ] JSONB columns for flexible fields with server-side default `'{}'::jsonb`
- [ ] PydanticJSONB TypeDecorator used for JSONB columns that map to Pydantic models
- [ ] Vector column on material_chunks (pgvector `VECTOR(1536)` type)
- [ ] Indexes: teacher_id, created_at, status on relevant tables
- [ ] GIN indexes on JSONB columns (accessibility_pack, metadata, keywords)
- [ ] CHECK constraints on status/enum columns
- [ ] `created_at` and `updated_at` with timezone-aware UTC defaults
- [ ] `uuid-utils` is a hard dependency in `pyproject.toml` (not optional)

**Tables (with columns):**

```
teachers
  id              UUID PK (uuid7)
  name            VARCHAR(255) NOT NULL
  email           VARCHAR(255) NOT NULL UNIQUE
  preferences     JSONB DEFAULT '{}'
  created_at      TIMESTAMPTZ DEFAULT now()

study_plans
  id              UUID PK (uuid7)
  teacher_id      UUID FK(teachers.id) NOT NULL, INDEX
  title           VARCHAR(500) NOT NULL
  grade           VARCHAR(50) NOT NULL
  standard        VARCHAR(20) NOT NULL  -- 'bncc'|'ccss'|'ngss'
  status          VARCHAR(20) NOT NULL DEFAULT 'draft'
                  CHECK(status IN ('draft','validated','refining','executing','done','failed'))
  draft           JSONB  -- StudyPlanDraft serialized
  final_plan      JSONB  -- Final reviewed plan
  accessibility_pack JSONB DEFAULT '{}'  -- GIN indexed
  metadata        JSONB DEFAULT '{}'  -- GIN indexed
  created_at      TIMESTAMPTZ DEFAULT now()
  updated_at      TIMESTAMPTZ DEFAULT now()

plan_steps
  id              UUID PK (uuid7)
  plan_id         UUID FK(study_plans.id) NOT NULL, INDEX
  position        INTEGER NOT NULL
  minutes         INTEGER NOT NULL CHECK(minutes > 0)
  title           VARCHAR(500) NOT NULL
  instructions    JSONB NOT NULL  -- list[str]
  activities      JSONB DEFAULT '[]'
  assessment      JSONB DEFAULT '[]'

materials
  id              UUID PK (uuid7)
  teacher_id      UUID FK(teachers.id) NOT NULL, INDEX
  title           VARCHAR(500) NOT NULL
  content_type    VARCHAR(50) NOT NULL  -- 'pdf'|'docx'|'txt'|'md'|'url'
  source_url      VARCHAR(2048)
  raw_text        TEXT
  metadata        JSONB DEFAULT '{}'  -- GIN indexed
  created_at      TIMESTAMPTZ DEFAULT now()

material_chunks
  id              UUID PK (uuid7)
  material_id     UUID FK(materials.id) NOT NULL, INDEX
  chunk_index     INTEGER NOT NULL
  text            TEXT NOT NULL
  embedding       VECTOR(1536)  -- pgvector; NULL on SQLite
  metadata        JSONB DEFAULT '{}'
  UNIQUE(material_id, chunk_index)

tutor_sessions
  id              UUID PK (uuid7)
  teacher_id      UUID FK(teachers.id) NOT NULL, INDEX
  learner_name    VARCHAR(255) NOT NULL
  agent_spec      JSONB NOT NULL  -- TutorAgentSpec serialized
  created_at      TIMESTAMPTZ DEFAULT now()

tutor_messages
  id              UUID PK (uuid7)
  session_id      UUID FK(tutor_sessions.id) NOT NULL, INDEX
  role            VARCHAR(20) NOT NULL  -- 'user'|'assistant'
  content         TEXT NOT NULL
  created_at      TIMESTAMPTZ DEFAULT now()

curriculum_objectives
  id              UUID PK (uuid7)
  system          VARCHAR(20) NOT NULL  -- 'bncc'|'ccss'|'ngss'
  code            VARCHAR(50) NOT NULL UNIQUE
  description     TEXT NOT NULL
  grade           VARCHAR(50) NOT NULL
  subject         VARCHAR(100) NOT NULL
  domain          VARCHAR(200) DEFAULT ''
  keywords        JSONB DEFAULT '[]'  -- GIN indexed

pipeline_runs
  id              UUID PK (uuid7)
  plan_id         UUID FK(study_plans.id), INDEX
  status          VARCHAR(20) NOT NULL DEFAULT 'pending'
  stage           VARCHAR(20)  -- current RunStage value
  events          JSONB DEFAULT '[]'
  started_at      TIMESTAMPTZ
  finished_at     TIMESTAMPTZ

export_variants
  id              UUID PK (uuid7)
  plan_id         UUID FK(study_plans.id) NOT NULL, INDEX
  format          VARCHAR(50) NOT NULL  -- ExportFormat value
  content         TEXT NOT NULL
  metadata        JSONB DEFAULT '{}'
  created_at      TIMESTAMPTZ DEFAULT now()
  UNIQUE(plan_id, format)

accessibility_reports
  id              UUID PK (uuid7)
  plan_id         UUID FK(study_plans.id) NOT NULL, INDEX
  score           INTEGER NOT NULL CHECK(score >= 0 AND score <= 100)
  status          VARCHAR(20) NOT NULL DEFAULT 'pending'
  details         JSONB DEFAULT '{}'
  created_at      TIMESTAMPTZ DEFAULT now()
```

**Branch Error Envelope (Codex / GPT-5.2 insight):**

Used in the LangGraph parallel fan-out: each branch returns an envelope so the
planner can proceed if at least one branch succeeds. This pattern keeps the
pipeline resilient to partial failures without crashing the entire graph.

```python
async def safe_branch(fn, *args, **kwargs):
    """Wrap a branch call so failures are captured, not raised."""
    try:
        return {"ok": True, "payload": await fn(*args, **kwargs), "error": None}
    except Exception as e:
        return {"ok": False, "payload": None, "error": str(e)}
```

**Idempotency Index for Pipeline Runs (Codex / GPT-5.2 insight):**

Prevents duplicate plan generation from retried requests. The unique constraint
on `(teacher_id, run_id)` guarantees that a retry with the same `run_id` is
safely rejected at the database level.

```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_study_plans_teacher_run
ON study_plans (teacher_id, run_id);
```

> **Implementation note:** This requires adding a `run_id UUID` column to the
> `study_plans` table (nullable for plans created outside a pipeline run). The
> index is partial -- it only covers rows where `run_id IS NOT NULL`.

**UUID v7 Compatibility Wrapper (GPT-5.2 / Codex critical finding):**

> **CRITICAL: `uuid.uuid7()` is Python 3.14+, NOT Python 3.13.** The stdlib
> `uuid` module in Python 3.13 does NOT have `uuid7()`. The project MUST use
> `uuid-utils` as a hard dependency (not optional) in `pyproject.toml`.

```python
# runtime/ailine_runtime/adapters/db/base.py — uuid7 compatibility wrapper
#
# uuid.uuid7() lands in Python 3.14 (PEP 761). On 3.13 and earlier, we use
# the uuid-utils package. This wrapper ensures zero-effort migration when
# the project upgrades to 3.14.

try:
    from uuid import uuid7 as _stdlib_uuid7

    def new_uuid7():
        """Generate UUID v7 via stdlib (Python 3.14+)."""
        return _stdlib_uuid7()

except ImportError:
    from uuid_utils import uuid7 as _utils_uuid7

    def new_uuid7():
        """Generate UUID v7 via uuid-utils (Python <3.14 fallback)."""
        return _utils_uuid7()
```

> **pyproject.toml entry:** `uuid-utils` must appear as a regular dependency
> (not in `[project.optional-dependencies]`). Document in a code comment that
> Python 3.14 will make this package unnecessary.

**SQLAlchemy Base Module (revised):**

```python
# runtime/ailine_runtime/adapters/db/base.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# --- UUID v7 compatibility wrapper ---
# uuid.uuid7() lands in Python 3.14 (PEP 761). On 3.13 and earlier,
# we use the uuid-utils package.
try:
    from uuid import uuid7 as _stdlib_uuid7

    def new_uuid7() -> uuid.UUID:
        """Generate UUID v7 via stdlib (Python 3.14+)."""
        return _stdlib_uuid7()

except ImportError:
    from uuid_utils import uuid7 as _utils_uuid7

    def new_uuid7() -> uuid.UUID:
        """Generate UUID v7 via uuid-utils (Python <3.14 fallback)."""
        return _utils_uuid7()


# Naming convention for constraints (Alembic autogenerate-friendly)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


def utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)
```

**JSONB + Pydantic TypeDecorator (GPT-5.2 / Codex pattern):**

Provides strict roundtrip serialization between Pydantic models and JSONB
columns. Writes use `model_dump(mode='json')` and reads use `model_validate`.
This ensures type safety at the database boundary.

```python
# runtime/ailine_runtime/adapters/db/types.py
from __future__ import annotations

import json
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

T = TypeVar("T", bound=BaseModel)


class PydanticJSONB(TypeDecorator, Generic[T]):
    """SQLAlchemy TypeDecorator that serializes/deserializes a Pydantic model
    to/from a JSONB column.

    Write path: model_dump(mode='json') -> JSONB
    Read path:  JSONB -> model_validate -> Pydantic instance

    On non-Postgres dialects (e.g. SQLite), falls back to TEXT with
    JSON serialization.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, pydantic_type: type[T], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._pydantic_type = pydantic_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        # SQLite fallback: store as TEXT
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: T | dict | None, dialect) -> dict | str | None:
        if value is None:
            return None
        if isinstance(value, BaseModel):
            dumped = value.model_dump(mode="json")
        else:
            dumped = value
        # On SQLite, serialize to JSON string
        if dialect.name != "postgresql":
            return json.dumps(dumped)
        return dumped

    def process_result_value(self, value: dict | str | None, dialect) -> T | None:
        if value is None:
            return None
        # On SQLite, value comes back as a JSON string
        if isinstance(value, str):
            value = json.loads(value)
        return self._pydantic_type.model_validate(value)
```

**Usage example in ORM model:**

```python
from .types import PydanticJSONB
from ailine_runtime.domain.entities.plan import AccessibilityPack

class StudyPlanModel(Base):
    # ... other columns ...
    accessibility_pack: Mapped[AccessibilityPack | None] = mapped_column(
        PydanticJSONB(AccessibilityPack), nullable=True
    )
```

**SQLAlchemy Pattern (model example):**

```python
# Excerpt from runtime/ailine_runtime/adapters/db/models.py
from sqlalchemy import (
    CheckConstraint, Column, DateTime, ForeignKey, Index,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .base import Base, new_uuid7, utcnow

class StudyPlanModel(Base):
    __tablename__ = "study_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teachers.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    grade: Mapped[str] = mapped_column(String(50), nullable=False)
    standard: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    draft: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    final_plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    accessibility_pack: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relationships
    teacher = relationship("TeacherModel", back_populates="study_plans")
    steps = relationship("PlanStepModel", back_populates="plan", cascade="all, delete-orphan")
    pipeline_runs = relationship("PipelineRunModel", back_populates="plan")
    export_variants = relationship("ExportVariantModel", back_populates="plan")
    accessibility_reports = relationship("AccessibilityReportModel", back_populates="plan")

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','validated','refining','executing','done','failed')",
            name="plan_status",
        ),
        Index("ix_study_plans_accessibility_pack", "accessibility_pack", postgresql_using="gin"),
        Index("ix_study_plans_metadata", metadata_, postgresql_using="gin"),
    )

class MaterialChunkModel(Base):
    __tablename__ = "material_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=new_uuid7
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materials.id"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1536), nullable=True)  # pgvector only
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")

    material = relationship("MaterialModel", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("material_id", "chunk_index", name="uq_chunk_material_index"),
    )
```

---

### S2-002: Alembic Migrations

**Description:** Set up Alembic for async SQLAlchemy migrations. Create the
initial migration that establishes all 11 tables, the pgvector extension,
HNSW index on embeddings, and GIN indexes on JSONB columns.

**Files:**
- `runtime/alembic.ini` (Alembic configuration pointing to async driver)
- `runtime/alembic/env.py` (async migration runner using `run_sync`)
- `runtime/alembic/script.py.mako` (migration template)
- `runtime/alembic/versions/001_initial_schema.py` (initial migration)

**Acceptance Criteria:**
- [ ] `CREATE EXTENSION IF NOT EXISTS vector;` executes before table creation
- [ ] All 11 tables created with correct types, constraints, and indexes
- [ ] HNSW index on `material_chunks.embedding` (cosine ops, m=16, ef_construction=128)
- [ ] GIN indexes on JSONB columns (accessibility_pack, metadata, keywords)
- [ ] Migration is reversible (downgrade drops tables + extension)
- [ ] Migration runs on Postgres (full) and SQLite (skips vector/GIN ops)
- [ ] `alembic.ini` uses `AILINE_DB_URL` environment variable for sqlalchemy.url
- [ ] Async env.py uses `async_engine_from_config` + `run_sync` pattern for asyncpg
- [ ] Connection pool configuration passed through to engine in env.py

**Alembic Async env.py (GPT-5.2 / Codex exact pattern):**

The async Alembic env.py must use `async_engine_from_config` with the `run_sync`
adapter to bridge Alembic's synchronous migration API with asyncpg's async
driver. This is the canonical pattern for SQLAlchemy 2.x async migrations.

```python
# runtime/alembic/env.py
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from ailine_runtime.adapters.db.base import Base  # target_metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL to stdout)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Synchronous callback passed to connection.run_sync()."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations via run_sync bridge."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No pool for migration runner
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connected to a live database)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

> **Key detail:** The migration runner uses `poolclass=pool.NullPool` because
> migrations are short-lived processes that should not maintain a connection pool.
> The application's session factory (S2-003) uses a full pool with `pool_pre_ping`.

**HNSW Index SQL:**

```sql
CREATE INDEX ix_material_chunks_embedding ON material_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 128);
```

**GIN Index examples:**

```sql
CREATE INDEX ix_study_plans_accessibility_pack ON study_plans
USING gin (accessibility_pack);

CREATE INDEX ix_curriculum_objectives_keywords ON curriculum_objectives
USING gin (keywords);
```

**Conditional logic for SQLite:**

```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # ... create all tables ...

    if is_postgres:
        # HNSW index (pgvector only)
        op.execute("""
            CREATE INDEX ix_material_chunks_embedding ON material_chunks
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 128);
        """)
        # GIN indexes (PostgreSQL only)
        op.create_index(
            "ix_study_plans_accessibility_pack",
            "study_plans", ["accessibility_pack"],
            postgresql_using="gin",
        )
```

---

### S2-003: UnitOfWork + Repository Pattern

**Description:** Implement async UnitOfWork and Repository classes that satisfy
the domain port protocols defined in `domain/ports/db.py`. The UoW wraps
SQLAlchemy `AsyncSession` transactions. Repositories translate between ORM
models and Pydantic domain entities.

**Files:**
- `runtime/ailine_runtime/adapters/db/session.py` (async engine + session factory)
- `runtime/ailine_runtime/adapters/db/uow.py` (SqlAlchemyUnitOfWork)
- `runtime/ailine_runtime/adapters/db/repositories.py` (PlanRepository, MaterialRepository, TutorSessionRepository, CurriculumRepository, PipelineRunRepository)
- `runtime/ailine_runtime/adapters/db/tenant.py` (TenantContext + TeacherId NewType)

**Acceptance Criteria:**
- [ ] `SqlAlchemyUnitOfWork` satisfies `UnitOfWork` protocol (isinstance check passes)
- [ ] UoW is an async context manager: auto-rollback on exception, explicit commit
- [ ] UoW uses `expire_on_commit=False` on session factory
- [ ] Connection pool: `pool_pre_ping=True`, `pool_size=5`, `max_overflow=5`, `pool_timeout=30`, `pool_recycle=1800` (ADR-052)
- [ ] Repository accessors on UoW are cached (lazy-initialized, reuse same instance)
- [ ] `PlanRepository.get()` returns `StudyPlanDraft` domain entity (translated from ORM)
- [ ] `PlanRepository.list()` supports cursor-based pagination using UUID v7 ordering
- [ ] `MaterialRepository` handles material + chunks in a single transaction
- [ ] All repositories satisfy the `Repository` protocol
- [ ] Session factory reads `AILINE_DB_URL` from settings and creates engine once
- [ ] All repository write and query methods require `TeacherId` parameter (not raw str)
- [ ] `teacher_id` NEVER accepted from request body schemas
- [ ] Cross-tenant isolation verified in integration tests (teacher_a / teacher_b fixtures)

**TeacherId NewType + TenantContext (GPT-5.2 / Codex exact pattern):**

Use `NewType` for compile-time type safety so that a raw `str` or `UUID` cannot
be accidentally passed where a `TeacherId` is expected. The `TenantContext`
FastAPI dependency extracts the teacher identity from the JWT/auth context ONLY.

```python
# runtime/ailine_runtime/adapters/db/tenant.py
from __future__ import annotations

import uuid
from typing import NewType

from pydantic import BaseModel
from fastapi import Depends

# NewType wrapper for type safety — prevents accidentally passing a raw str/UUID
TeacherId = NewType("TeacherId", uuid.UUID)


class TenantContext(BaseModel):
    """Immutable tenant identity derived from auth context, never from user input."""

    teacher_id: TeacherId

    model_config = {"frozen": True}


async def get_tenant_ctx(
    # user=Depends(require_authenticated_user)  # wire to real auth dependency
) -> TenantContext:
    """FastAPI dependency: extracts tenant from the authenticated user's JWT.

    The teacher_id is read from the auth token claims. It is NEVER accepted
    from the request body. This is the single source of truth for tenant
    identity in every request.
    """
    # TODO: Wire to real auth dependency (Sprint 3+)
    # return TenantContext(teacher_id=TeacherId(user.teacher_id))
    raise NotImplementedError("Wire to real auth in Sprint 3+")
```

> **Request body enforcement:** All request body Pydantic schemas (e.g.,
> `CreatePlanRequest`, `UploadMaterialRequest`) must NOT include a `teacher_id`
> field. The tenant identity flows exclusively through `TenantContext`.

**Session Factory with Full Pool Configuration (GPT-5.2 / Codex exact pattern):**

```python
# runtime/ailine_runtime/adapters/db/session.py
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ailine_runtime.shared.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.db.url,
            echo=settings.db.echo,
            # Pool configuration (GPT-5.2 / Codex recommended values)
            pool_pre_ping=True,     # Detect stale connections before use
            pool_size=5,            # Reduced per GPT-5.2 Feb 12 consultation (ADR-052)
            max_overflow=5,         # Conservative to avoid connection exhaustion
            pool_timeout=30,        # Seconds to wait for a connection
            pool_recycle=1800,      # Recycle connections after 30 minutes
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,  # Critical for async: avoid lazy-load traps
        )
    return _session_factory
```

> **Why `expire_on_commit=False`:** In async SQLAlchemy, accessing attributes
> on an expired ORM instance triggers a lazy load, which requires an active
> event loop and session. Setting `expire_on_commit=False` prevents this trap
> by keeping attribute values in memory after commit.

**UnitOfWork with Repository Accessor Cache (GPT-5.2 / Codex exact pattern):**

Repository accessors are lazily initialized and cached on the UoW instance.
This ensures that all repositories within a single UoW share the same session.

```python
# runtime/ailine_runtime/adapters/db/uow.py
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .repositories import (
    PlanRepository,
    MaterialRepository,
    TutorSessionRepository,
    CurriculumRepository,
    PipelineRunRepository,
)


class SqlAlchemyUnitOfWork:
    """Async Unit of Work wrapping a SQLAlchemy session.

    Usage:
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            plan = await uow.plans.get(plan_id, teacher_id=tid)
            await uow.plans.save(plan, teacher_id=tid)
            await uow.commit()
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        # Cached repository accessors
        self._plans: PlanRepository | None = None
        self._materials: MaterialRepository | None = None
        self._tutor_sessions: TutorSessionRepository | None = None
        self._curriculum: CurriculumRepository | None = None
        self._pipeline_runs: PipelineRunRepository | None = None

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            if self._session:
                await self._session.close()
                self._session = None
            # Clear cached repositories
            self._plans = None
            self._materials = None
            self._tutor_sessions = None
            self._curriculum = None
            self._pipeline_runs = None

    async def commit(self) -> None:
        assert self._session is not None, "UoW not entered"
        await self._session.commit()

    async def rollback(self) -> None:
        assert self._session is not None, "UoW not entered"
        await self._session.rollback()

    @property
    def session(self) -> AsyncSession:
        assert self._session is not None, "UoW not entered"
        return self._session

    # --- Cached repository accessors ---

    @property
    def plans(self) -> PlanRepository:
        if self._plans is None:
            self._plans = PlanRepository(self.session)
        return self._plans

    @property
    def materials(self) -> MaterialRepository:
        if self._materials is None:
            self._materials = MaterialRepository(self.session)
        return self._materials

    @property
    def tutor_sessions(self) -> TutorSessionRepository:
        if self._tutor_sessions is None:
            self._tutor_sessions = TutorSessionRepository(self.session)
        return self._tutor_sessions

    @property
    def curriculum(self) -> CurriculumRepository:
        if self._curriculum is None:
            self._curriculum = CurriculumRepository(self.session)
        return self._curriculum

    @property
    def pipeline_runs(self) -> PipelineRunRepository:
        if self._pipeline_runs is None:
            self._pipeline_runs = PipelineRunRepository(self.session)
        return self._pipeline_runs
```

> **Safe `__aexit__` pattern:** Rollback is wrapped in `try/finally` to ensure
> `session.close()` always runs, even if rollback itself raises. Repository
> caches are cleared on exit to prevent stale session references.

**Cursor-based pagination pattern:**

```python
async def list(
    self,
    *,
    teacher_id: TeacherId,  # Mandatory — enforces tenant isolation
    after: uuid.UUID | None = None,
    limit: int = 20,
) -> list[StudyPlanDraft]:
    stmt = (
        select(StudyPlanModel)
        .where(StudyPlanModel.teacher_id == teacher_id)
        .order_by(StudyPlanModel.id)
    )
    if after:
        stmt = stmt.where(StudyPlanModel.id > after)
    stmt = stmt.limit(limit)
    result = await self._session.execute(stmt)
    return [self._to_domain(row) for row in result.scalars().all()]
```

> **Note:** `teacher_id` is now mandatory (not optional) on the `list()` method.
> This enforces tenant isolation at the repository level. The `after` cursor
> uses UUID v7's time-ordering property for efficient keyset pagination.

**Cross-Tenant Integration Test Fixtures:**

```python
# tests/integration/conftest.py

import pytest
from ailine_runtime.adapters.db.tenant import TeacherId
from ailine_runtime.adapters.db.base import new_uuid7


@pytest.fixture
def teacher_a() -> TeacherId:
    """Stable tenant identity for teacher A in cross-tenant tests."""
    return TeacherId(new_uuid7())


@pytest.fixture
def teacher_b() -> TeacherId:
    """Stable tenant identity for teacher B in cross-tenant tests."""
    return TeacherId(new_uuid7())


# Example cross-tenant isolation test:
#
# async def test_teacher_a_cannot_see_teacher_b_plans(uow, teacher_a, teacher_b):
#     async with uow:
#         await uow.plans.save(some_plan, teacher_id=teacher_a)
#         await uow.commit()
#     async with uow:
#         plans = await uow.plans.list(teacher_id=teacher_b)
#         assert len(plans) == 0  # teacher_b sees nothing from teacher_a
```

---

### S2-004: Docker Compose (Postgres + pgvector + Redis)

**Description:** Docker Compose stack for local development with Postgres 17
(pgvector extension), Redis 7, and the API service. Includes health checks,
private networking, and volume persistence.

**Files:**
- `docker-compose.yml` (root-level Compose file)
- `runtime/Dockerfile` (multi-stage Python build, non-root)
- `.env.example` (template for environment variables)

**Acceptance Criteria:**
- [ ] `pgvector/pgvector:pg17` image with healthcheck (`pg_isready`)
- [ ] `redis:7-alpine` image with healthcheck (`redis-cli ping`)
- [ ] API service Dockerfile: multi-stage build, non-root user, `uv` for deps
- [ ] Private bridge network `ailine-internal` for DB/Redis
- [ ] Named volume `pgdata` for Postgres data persistence
- [ ] `.env.example` with all required environment variables documented
- [ ] Port collision check: 5432, 6379, 8000 (document alternatives)
- [ ] `COMPOSE_PROJECT_NAME=ailine` set in `.env`

**Infrastructure Scope Note (Gemini recommendation):**

Do NOT introduce Redis or Chroma unless absolutely necessary for performance.
For the demo/pre-MVP stage, Postgres handles everything: application data and
vector search (via pgvector). Redis is optional and should only be added when
there is a concrete need for caching or pub-sub. Keep the stack minimal to
reduce operational complexity and startup time.

**docker-compose.yml:**

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: ailine
      POSTGRES_USER: ailine
      POSTGRES_PASSWORD: ${AILINE_DB_PASSWORD:-ailine_dev}
    ports:
      - "${AILINE_DB_PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ailine -d ailine"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - ailine-internal

  redis:
    image: redis:7-alpine
    ports:
      - "${AILINE_REDIS_PORT:-6379}:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - ailine-internal

  api:
    build:
      context: ./runtime
      dockerfile: Dockerfile
    ports:
      - "${AILINE_API_PORT:-8000}:8000"
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - ailine-internal

volumes:
  pgdata:

networks:
  ailine-internal:
    driver: bridge
```

**Dockerfile (multi-stage, non-root):**

```dockerfile
# ---- Build stage ----
FROM python:3.13-slim AS builder
WORKDIR /build
RUN pip install uv
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# ---- Runtime stage ----
FROM python:3.13-slim AS runtime
RUN groupadd -r ailine && useradd --no-log-init -r -g ailine ailine
WORKDIR /app
COPY --from=builder /build/.venv /app/.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
USER ailine
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "ailine_runtime.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

**.env.example:**

```bash
COMPOSE_PROJECT_NAME=ailine

# Database
AILINE_DB_URL=postgresql+asyncpg://ailine:ailine_dev@postgres:5432/ailine
AILINE_DB_PASSWORD=ailine_dev
AILINE_DB_PORT=5432

# Redis
AILINE_REDIS_URL=redis://redis:6379/0
AILINE_REDIS_PORT=6379

# API
AILINE_API_PORT=8000

# LLM keys (fill in with real keys)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=

# Embedding config
AILINE_EMBEDDING_PROVIDER=gemini
AILINE_EMBEDDING_MODEL=gemini-embedding-001
AILINE_EMBEDDING_DIMENSIONS=1536

# Vector store
AILINE_VECTORSTORE_PROVIDER=pgvector
```

---

### S2-005: i18n Data Files

**Description:** Create translation JSON files for PT-BR (primary), EN, and ES.
These files are loaded by the `t()` function defined in
`runtime/ailine_runtime/shared/i18n.py` (Sprint 1). Covers UI labels, error
messages, pipeline status messages, accessibility terms, curriculum terms,
and tutor interaction strings.

**Files:**
- `runtime/ailine_runtime/data/i18n/pt-BR.json` (primary, ~200 keys)
- `runtime/ailine_runtime/data/i18n/en.json` (~200 keys)
- `runtime/ailine_runtime/data/i18n/es.json` (~200 keys)

**Acceptance Criteria:**
- [ ] ~200 keys per file covering all domains (plan, material, tutor, accessibility, pipeline, errors, common UI)
- [ ] Portuguese (Brazil) as primary reference; EN and ES as translations
- [ ] `t("plan.title", "pt-BR")` returns correct translation
- [ ] `t("missing.key", "pt-BR")` falls back to EN, then returns key itself
- [ ] Keys organized by namespace: `plan.*`, `material.*`, `tutor.*`, `accessibility.*`, `pipeline.*`, `error.*`, `common.*`
- [ ] Accessibility terms use official Brazilian Portuguese terminology (e.g., "Transtorno do Espectro Autista", "TDAH", "Deficiencia Visual")

**Key namespace examples:**

```json
{
  "common.save": "Salvar",
  "common.cancel": "Cancelar",
  "common.loading": "Carregando...",
  "common.error": "Erro",
  "common.success": "Sucesso",

  "plan.title": "Plano de Estudo",
  "plan.create": "Criar Plano de Estudo",
  "plan.status.draft": "Rascunho",
  "plan.status.validated": "Validado",
  "plan.status.done": "Concluido",
  "plan.status.failed": "Falhou",
  "plan.step": "Etapa",
  "plan.objectives": "Objetivos de Aprendizagem",

  "material.upload": "Enviar Material",
  "material.processing": "Processando material...",
  "material.chunks_created": "{count} trechos criados",

  "tutor.session_start": "Sessao de Tutoria Iniciada",
  "tutor.thinking": "O tutor esta pensando...",
  "tutor.check_understanding": "Vamos verificar se voce entendeu?",

  "accessibility.autism": "Transtorno do Espectro Autista (TEA)",
  "accessibility.adhd": "Transtorno do Deficit de Atencao e Hiperatividade (TDAH)",
  "accessibility.visual": "Deficiencia Visual",
  "accessibility.hearing": "Deficiencia Auditiva",
  "accessibility.motor": "Deficiencia Motora",
  "accessibility.learning": "Dificuldade de Aprendizagem",
  "accessibility.support_low": "Suporte Leve",
  "accessibility.support_medium": "Suporte Moderado",
  "accessibility.support_high": "Suporte Intensivo",

  "pipeline.started": "Pipeline iniciado",
  "pipeline.stage.planner": "Planejando...",
  "pipeline.stage.validate": "Validando...",
  "pipeline.stage.executor": "Executando...",
  "pipeline.complete": "Pipeline concluido com sucesso",
  "pipeline.failed": "Erro no pipeline: {reason}",

  "error.not_found": "Recurso nao encontrado",
  "error.validation": "Dados invalidos: {details}",
  "error.rate_limit": "Limite de requisicoes atingido. Tente novamente em {seconds}s",
  "error.provider": "Erro no provedor: {provider}"
}
```

---

## Dependencies

**Requires:** Sprint 1 (clean architecture) -- domain entities, port protocols,
shared config, DI container, and i18n infrastructure must be in place.

**Produces for Sprint 3:** ORM models (especially `material_chunks` with VECTOR
column), session factory, UoW, Docker Compose stack with pgvector.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| pgvector VECTOR type unsupported on SQLite | Medium | Conditional column: use TEXT/NULL on SQLite, VECTOR on Postgres. Migration checks `bind.dialect.name`. |
| **uuid.uuid7() NOT in Python 3.13 stdlib** | **High** | **`uuid-utils==0.14.0` as HARD dependency (non-optional). Compatibility wrapper tries stdlib first (for 3.14+), falls back to uuid-utils. Documented in base.py and pyproject.toml.** |
| JSONB columns not on SQLite | Medium | SQLAlchemy `JSONB` type auto-degrades to JSON on SQLite. PydanticJSONB TypeDecorator handles TEXT fallback. Test both paths. |
| GIN/HNSW indexes Postgres-only | Low | Migration conditionally creates indexes only on Postgres. |
| Port 5432/6379/8000 already in use | Low | All ports configurable via `.env` variables with defaults. |
| Large migration on first run | Low | Single initial migration; squash-friendly in pre-MVP. |
| Stale DB connections in long-running app | Medium | `pool_pre_ping=True` + `pool_recycle=1800` detects and replaces stale connections. |
| Lazy-load traps in async SQLAlchemy | High | `expire_on_commit=False` on session factory prevents post-commit lazy loads. |
| Cross-tenant data leakage | Critical | `TeacherId` NewType + mandatory parameter on all repo methods + integration test fixtures (`teacher_a`/`teacher_b`). |

---

## Testing Plan

- **Unit tests:** ORM model instantiation, uuid7 generation (via wrapper), domain<->ORM translation, PydanticJSONB roundtrip
- **Integration tests (Docker Postgres):** Migration up/down, CRUD via repositories, UoW commit/rollback, pagination, **cross-tenant isolation (teacher_a/teacher_b)**
- **SQLite fallback test:** Migration runs, basic CRUD works (vector ops skipped), PydanticJSONB TEXT fallback works
- **Docker Compose smoke test:** `docker compose up -d`, wait healthy, run `alembic upgrade head`, hit `/health`

---

## Expert Consultation Notes

**Source:** GPT-5.2 / Codex expert consultation (2026-02-11)
**Consulted by:** Lead agent via Zen PAL MCP

### Finding 1: uuid.uuid7() Availability (CRITICAL)

**Issue:** The original sprint plan assumed `uuid.uuid7()` might be available in
Python 3.13. This is INCORRECT. `uuid.uuid7()` is part of PEP 761 and ships
with **Python 3.14**, not 3.13.

**Impact:** High -- calling `uuid.uuid7()` on Python 3.13 raises `AttributeError`,
breaking all primary key generation.

**Resolution:**
- `uuid-utils==0.14.0` is a **hard dependency** (not optional) in `pyproject.toml`
- A compatibility wrapper (`new_uuid7()`) in `base.py` tries the stdlib first
  (future-proofing for 3.14 upgrade) and falls back to `uuid_utils.uuid7()`
- The old `uuid7_default()` function name is replaced with `new_uuid7()` for
  clarity that this is not a simple default value callback
- All ORM models use `default=new_uuid7` (not `default=uuid7_default`)

### Finding 2: SQLAlchemy Async Session Configuration

**Issue:** The original session factory lacked production-grade pool settings.

**Resolution -- exact pool parameters:**
- `pool_pre_ping=True` -- Detect stale/broken connections before checkout
- `pool_size=5` -- Reduced per GPT-5.2 Feb 12 consultation (ADR-052)
- `max_overflow=5` -- Conservative to avoid connection exhaustion
- `pool_timeout=30` -- Max seconds to wait for a connection from the pool
- `pool_recycle=1800` -- Replace connections older than 30 minutes (prevents
  server-side timeout kills)
- `expire_on_commit=False` on `async_sessionmaker` -- Prevents lazy-load traps
  that are fatal in async code (accessing an expired attribute triggers a sync
  I/O call that blocks the event loop)

### Finding 3: Repository Accessor Cache Pattern in UoW

**Issue:** Original UoW did not show how repositories are accessed.

**Resolution:** Repository instances are lazily created as `@property` accessors
on the UoW, cached for the lifetime of the context manager. All repositories
within a single UoW share the same `AsyncSession`. Caches are cleared in
`__aexit__` to prevent stale session references.

### Finding 4: JSONB + Pydantic TypeDecorator

**Issue:** JSONB columns storing Pydantic models need strict serialization.

**Resolution:** A `PydanticJSONB` TypeDecorator that:
- **Write path:** Calls `model_dump(mode='json')` to produce a JSON-serializable dict
- **Read path:** Calls `model_validate()` to reconstruct the Pydantic instance
- **SQLite fallback:** Uses `Text` type with `json.dumps()`/`json.loads()`
- `cache_ok = True` for SQLAlchemy's type caching optimization

### Finding 5: Alembic Async env.py

**Issue:** The original env.py pattern was correct but lacked pool configuration
detail and dialect options.

**Resolution:**
- Use `poolclass=pool.NullPool` for the migration runner (short-lived process)
- `async_engine_from_config` + `connection.run_sync(do_run_migrations)` is the
  canonical pattern for SQLAlchemy 2.x async migrations with asyncpg
- Added `dialect_opts={"paramstyle": "named"}` for offline mode

### Finding 6: TenantContext + TeacherId NewType

**Issue:** Original plan used `teacher_id: str` which allows accidental misuse.

**Resolution:**
- `TeacherId = NewType("TeacherId", uuid.UUID)` provides compile-time type safety
- `TenantContext` is a frozen Pydantic model extracted from JWT/auth context
- `teacher_id` must NEVER appear in request body schemas
- All repository methods require `TeacherId` as a mandatory parameter (not optional)
- Integration tests use `teacher_a` / `teacher_b` fixtures to verify isolation:
  teacher A's data must never be visible to teacher B's queries

### Finding 7: Safe UoW __aexit__ Pattern

**Issue:** Original `__aexit__` could leak the session if rollback raised.

**Resolution:** Wrap rollback in `try/finally` to guarantee `session.close()` and
cache cleanup always execute, even if the rollback itself fails. This prevents
connection leaks under error conditions.
