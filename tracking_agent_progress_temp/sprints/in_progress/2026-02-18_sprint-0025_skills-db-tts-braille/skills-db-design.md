# Skills DB Persistence — Design Document (F-175)

## 1. Overview

Replace the current filesystem-based skill storage (`skills/*/SKILL.md`) with PostgreSQL persistence, enabling CRUD operations, versioning, teacher ownership, ratings, and pgvector similarity search. The existing `SkillRegistry` becomes a thin facade that delegates to a `SkillRepository` port backed by a Postgres adapter.

## 2. Current Architecture

### 2.1 Filesystem Layout
```
skills/
  accessibility-adaptor/SKILL.md
  lesson-planner/SKILL.md
  ... (17 skills total)
```

### 2.2 Existing Code Modules

| Module | Path | Role | DB Impact |
|--------|------|------|-----------|
| `SkillDefinition` | `agents/.../skills/registry.py:10-16` | Pydantic model: name, description, instructions, metadata | Maps to `skills` table |
| `SkillRegistry` | `agents/.../skills/registry.py:19-86` | In-memory dict, scan(), get_by_name(), get_prompt_fragment() | Refactor to use SkillRepository |
| `parse_skill_md()` | `agents/.../skills/loader.py:15-72` | Parse YAML frontmatter + markdown body | Keep for seed migration |
| `validate_skill_spec()` | `agents/.../skills/spec.py:86-196` | Validate against agentskills.io spec | Use on API create/update |
| `compose_skills_fragment()` | `agents/.../skills/composer.py:103-195` | Token-budget prompt composition from ActivatedSkill list | No change (source-agnostic) |
| `AccessibilityPolicy` | `agents/.../skills/accessibility_policy.py` | 7 profiles -> 17 skills mapping, resolve_accessibility_skills() | Filter by DB-available skills |

## 3. SQLAlchemy ORM Models

### 3.1 SkillRow

```python
class SkillRow(Base):
    """Persisted skill definition (replaces SKILL.md files)."""

    __tablename__ = "skills"
    __table_args__ = (
        Index("ix_skills_teacher", "teacher_id"),
        Index("ix_skills_is_active", "is_active"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    instructions_md: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    license: Mapped[str] = mapped_column(String(255), default="")
    compatibility: Mapped[str] = mapped_column(String(500), default="")
    allowed_tools: Mapped[str] = mapped_column(Text, default="")
    # teacher_id NULL = system skill (seeded from filesystem)
    teacher_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    forked_from_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=_utcnow
    )

    # Note: embedding VECTOR(1536) column added via migration only
    # (same pattern as ChunkRow — keeps ORM portable to aiosqlite for tests)

    # Relationships
    versions: Mapped[list[SkillVersionRow]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
    ratings: Mapped[list[SkillRatingRow]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
```

**Key design decisions:**
- `slug` replaces `name` as the unique identifier (matches agentskills.io spec naming rules)
- `teacher_id` is nullable: NULL = system skill (seeded from filesystem), non-NULL = teacher-created
- `forked_from_id` self-references to track skill lineage when teachers fork system skills
- `is_system` flag prevents teachers from deleting/modifying system skills
- `embedding` column added via raw SQL in migration (same pattern as `chunks` table, ADR-053)
- `metadata_json` uses JSON type (auto-JSONB on Postgres, compatible with aiosqlite in tests)

### 3.2 SkillVersionRow

```python
class SkillVersionRow(Base):
    """Version history for skill content changes."""

    __tablename__ = "skill_versions"
    __table_args__ = (
        UniqueConstraint("skill_id", "version", name="uq_skill_version"),
        Index("ix_skill_versions_skill", "skill_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    skill_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    instructions_md: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    change_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    skill: Mapped[SkillRow] = relationship(back_populates="versions")
```

**Notes:**
- Version 1 is created automatically on skill creation
- Each update increments version and creates a new SkillVersionRow
- `change_summary` captures what changed (optional, for audit trail)

### 3.3 SkillRatingRow

```python
class SkillRatingRow(Base):
    """Teacher rating for a skill (1-5 stars)."""

    __tablename__ = "skill_ratings"
    __table_args__ = (
        UniqueConstraint("skill_id", "user_id", name="uq_skill_user_rating"),
        Index("ix_skill_ratings_skill", "skill_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    skill_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    skill: Mapped[SkillRow] = relationship(back_populates="ratings")
```

**Notes:**
- One rating per user per skill (upsert on re-rating)
- `avg_rating` and `rating_count` on SkillRow are denormalized for query performance
- Updated via trigger or application logic on INSERT/UPDATE/DELETE

### 3.4 TeacherSkillSetRow

```python
class TeacherSkillSetRow(Base):
    """Named collection of skills configured by a teacher (preset)."""

    __tablename__ = "teacher_skill_sets"
    __table_args__ = (
        UniqueConstraint("teacher_id", "name", name="uq_teacher_skillset_name"),
        Index("ix_teacher_skill_sets_teacher", "teacher_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid7_str)
    teacher_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    skill_slugs_json: Mapped[list] = mapped_column(JSON, default=list)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=_utcnow
    )
```

**Notes:**
- Deferred to Sprint 26 (F-178), but schema created in migration 0004 for forward compatibility
- `skill_slugs_json` is a JSON array of skill slug strings (not FKs, since skills may be deleted)
- `is_default` marks one preset per teacher as the auto-applied set

## 4. Migration 0004 — Skills Tables

### 4.1 Alembic Migration Structure

```python
"""Skills DB persistence: skills, skill_versions, skill_ratings, teacher_skill_sets.

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-XX

Adds 4 new tables for the Skills system:
- skills: main skill definitions with pgvector embedding
- skill_versions: version history
- skill_ratings: teacher ratings (1-5)
- teacher_skill_sets: named skill presets per teacher
"""

revision: str = "0004"
down_revision: str = "0003"
```

### 4.2 SQL Operations

1. Create `skills` table with all columns except `embedding`
2. Conditionally add `embedding vector(1536)` column (Postgres only, same pattern as chunks)
3. Create HNSW index: `CREATE INDEX ix_skills_embedding ON skills USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 128)`
4. Create `skill_versions` table
5. Create `skill_ratings` table
6. Create `teacher_skill_sets` table
7. Create all indexes and constraints

### 4.3 Index Strategy

| Table | Index | Type | Purpose |
|-------|-------|------|---------|
| skills | `ix_skills_slug` | UNIQUE (B-tree) | Lookup by slug |
| skills | `ix_skills_teacher` | B-tree | Filter by teacher |
| skills | `ix_skills_is_active` | B-tree | Active-only queries |
| skills | `ix_skills_embedding` | HNSW (vector_cosine_ops) | Similarity search |
| skill_versions | `ix_skill_versions_skill` | B-tree | Version history per skill |
| skill_versions | `uq_skill_version` | UNIQUE (skill_id, version) | Prevent duplicate versions |
| skill_ratings | `ix_skill_ratings_skill` | B-tree | Ratings per skill |
| skill_ratings | `uq_skill_user_rating` | UNIQUE (skill_id, user_id) | One rating per user |
| teacher_skill_sets | `ix_teacher_skill_sets_teacher` | B-tree | Presets per teacher |
| teacher_skill_sets | `uq_teacher_skillset_name` | UNIQUE (teacher_id, name) | Unique preset names |

### 4.4 HNSW Parameters

Following the existing pattern from migration 0001 (chunks table):
- `m = 16` (connections per layer, balances recall vs build time)
- `ef_construction = 128` (build-time search width, higher = better recall)
- `vector_cosine_ops` (cosine similarity, matches gemini-embedding-001 output)

With only 17 system skills initially (growing to maybe 100-200), HNSW overhead is negligible. The index is future-proofing for when teachers create custom skills.

## 5. SkillRepository Protocol

### 5.1 Port Definition

Location: `runtime/ailine_runtime/domain/ports/skills.py` (new file)

```python
from __future__ import annotations
from typing import Protocol, runtime_checkable
from agents.ailine_agents.skills.registry import SkillDefinition


@runtime_checkable
class SkillRepository(Protocol):
    """Port for skill persistence and retrieval."""

    # --- CRUD ---
    async def get_by_slug(self, slug: str) -> SkillDefinition | None:
        """Retrieve a single active skill by slug."""
        ...

    async def list_all(
        self, *, active_only: bool = True, system_only: bool = False
    ) -> list[SkillDefinition]:
        """List all skills, optionally filtered."""
        ...

    async def create(
        self,
        skill: SkillDefinition,
        *,
        teacher_id: str | None = None,
        is_system: bool = False,
    ) -> str:
        """Create a new skill. Returns the generated ID."""
        ...

    async def update(
        self,
        slug: str,
        *,
        instructions_md: str | None = None,
        description: str | None = None,
        metadata: dict[str, str] | None = None,
        change_summary: str = "",
    ) -> None:
        """Update a skill (creates a new version)."""
        ...

    async def soft_delete(self, slug: str) -> None:
        """Soft-delete a skill (set is_active=False)."""
        ...

    # --- Search ---
    async def search_by_text(
        self, query: str, *, limit: int = 10
    ) -> list[SkillDefinition]:
        """Full-text search in slug + description."""
        ...

    async def search_similar(
        self, embedding: list[float], *, limit: int = 5
    ) -> list[SkillDefinition]:
        """Vector similarity search using pgvector."""
        ...

    # --- Teacher-specific ---
    async def list_by_teacher(self, teacher_id: str) -> list[SkillDefinition]:
        """List skills created by a specific teacher."""
        ...

    async def fork(
        self, source_slug: str, *, teacher_id: str
    ) -> str:
        """Fork a skill to a teacher's collection. Returns new skill ID."""
        ...

    # --- Ratings ---
    async def rate(
        self, slug: str, *, user_id: str, score: int, comment: str = ""
    ) -> None:
        """Rate a skill (1-5). Upserts on re-rating."""
        ...

    # --- Embedding ---
    async def update_embedding(
        self, slug: str, embedding: list[float]
    ) -> None:
        """Update the pgvector embedding for a skill."""
        ...
```

### 5.2 Adapter: PostgresSkillRepository

Location: `runtime/ailine_runtime/adapters/db/skill_repository.py` (new file)

Key implementation notes:
- Uses `async_sessionmaker` from existing container (same pattern as other repos)
- `search_similar()` uses pgvector `<=>` operator (cosine distance)
- `fork()` copies skill row with new teacher_id and forked_from_id
- `rate()` uses INSERT ON CONFLICT UPDATE (upsert), then recalculates avg_rating
- `update()` increments version, creates SkillVersionRow, updates SkillRow

### 5.3 Adapter: FakeSkillRepository (for testing)

Location: `runtime/ailine_runtime/adapters/db/fake_skill_repository.py` (new file)

In-memory dict-based implementation for unit tests (same pattern as FakeTTS).

## 6. Seed Migration Strategy

### 6.1 Approach

A data seed script (not an Alembic migration) that runs on first startup or via CLI:

```bash
uv run python -m ailine_runtime.cli.seed_skills
```

### 6.2 Steps

1. Scan `skills/` directory using existing `parse_skill_md()` from `loader.py`
2. For each of the 17 SKILL.md files:
   a. Parse frontmatter + body into SkillDefinition
   b. Validate with `validate_skill_spec()` from `spec.py`
   c. Generate embedding via `gemini-embedding-001` (description + first 500 chars of instructions)
   d. Insert into `skills` table with `is_system=True`, `teacher_id=NULL`
   e. Create initial SkillVersionRow (version=1)
3. Log results: X skills seeded, Y skipped (validation errors)

### 6.3 Idempotency

- Use `INSERT ... ON CONFLICT (slug) DO UPDATE` to handle re-runs
- Only update if the filesystem version is newer (compare instructions_md hash)
- Never delete DB skills that no longer exist on filesystem (teacher may have forked them)

### 6.4 Embedding Generation

```python
from google import genai

client = genai.Client(api_key=settings.google_api_key)

async def generate_skill_embedding(skill: SkillDefinition) -> list[float]:
    text = f"{skill.description}\n\n{skill.instructions[:2000]}"
    result = await client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config={"output_dimensionality": 1536},
    )
    return result.embeddings[0].values
```

## 7. SkillRegistry Refactoring

### 7.1 Current Interface

```python
class SkillRegistry:
    def scan(self, directory) -> int           # Load from filesystem
    def get_by_name(self, name) -> SkillDefinition | None
    def list_names(self) -> list[str]
    def get_prompt_fragment(self, names) -> str
```

### 7.2 Refactored Interface

```python
class SkillRegistry:
    def __init__(
        self,
        *,
        repository: SkillRepository | None = None,
        fallback_dirs: list[str] | None = None,
    ) -> None:
        """Initialize with DB repository (primary) and filesystem fallback."""
        self._repo = repository
        self._fallback_dirs = fallback_dirs or []
        self._cache: dict[str, SkillDefinition] = {}

    async def initialize(self) -> int:
        """Load skills from DB (or filesystem fallback). Returns count loaded."""
        if self._repo:
            skills = await self._repo.list_all(active_only=True)
            for s in skills:
                self._cache[s.name] = s
        else:
            # Filesystem fallback (dev without DB, tests)
            for d in self._fallback_dirs:
                self.scan(d)
        return len(self._cache)

    def scan(self, directory) -> int:
        """Legacy filesystem scan (kept for backward compatibility)."""
        ...  # existing implementation unchanged

    def get_by_name(self, name) -> SkillDefinition | None:
        return self._cache.get(name)

    def list_names(self) -> list[str]:
        return sorted(self._cache.keys())

    def get_prompt_fragment(self, names) -> str:
        ...  # existing implementation unchanged
```

### 7.3 Integration Points

1. **Container (DI):** `container.py` creates SkillRepository and passes to SkillRegistry
2. **Startup:** `app.py` lifespan calls `registry.initialize()` on app startup
3. **Agent deps:** `AgentDeps.skill_registry` remains unchanged (transparent to agents)
4. **API router:** New `/v1/skills` endpoints use SkillRepository directly (not SkillRegistry)

### 7.4 Backward Compatibility

- SkillRegistry still supports `scan()` for filesystem loading
- If no SkillRepository is provided (e.g., tests), falls back to filesystem
- Existing `SkillPromptComposer` and `AccessibilityPolicy` work unchanged
- No changes needed to `AgentDeps`, `RunState`, or `TutorGraphState`

## 8. Entity Relationship Diagram

```
users (from RBAC)
  |
  |-- 1:N --> skills (teacher_id, nullable for system skills)
  |              |
  |              |-- 1:N --> skill_versions (version history)
  |              |-- 1:N --> skill_ratings (teacher ratings)
  |              |-- self-ref --> skills (forked_from_id)
  |
  |-- 1:N --> teacher_skill_sets (named presets, Sprint 26)
```

## 9. Test Plan for F-175

| Test | Type | Count |
|------|------|-------|
| SkillRow/SkillVersionRow/SkillRatingRow/TeacherSkillSetRow ORM mapping | Unit | 8 |
| SkillDefinition -> SkillRow mapping (round-trip) | Unit | 4 |
| FakeSkillRepository CRUD | Unit | 8 |
| PostgresSkillRepository CRUD (Docker Postgres) | Integration | 8 |
| PostgresSkillRepository vector search | Integration | 4 |
| PostgresSkillRepository fork + rate | Integration | 4 |
| Seed migration: 17 skills loaded from filesystem | Integration | 2 |
| SkillRegistry with DB backend | Integration | 4 |
| SkillRegistry filesystem fallback | Unit | 2 |
| Migration 0004 up/down | Integration | 2 |
| **Total** | | **46** |

## 10. Files to Create/Modify

### New Files
| File | Purpose |
|------|---------|
| `runtime/ailine_runtime/domain/ports/skills.py` | SkillRepository Protocol |
| `runtime/ailine_runtime/adapters/db/skill_repository.py` | Postgres adapter |
| `runtime/ailine_runtime/adapters/db/fake_skill_repository.py` | Test adapter |
| `runtime/.../alembic/versions/2026_02_XX_0004_skills_persistence.py` | Migration |
| `runtime/ailine_runtime/cli/seed_skills.py` | Seed script |
| `runtime/tests/test_skill_repository.py` | Repository tests |
| `runtime/tests/test_skill_db_models.py` | ORM model tests |

### Modified Files
| File | Change |
|------|--------|
| `runtime/ailine_runtime/adapters/db/models.py` | Add SkillRow, SkillVersionRow, SkillRatingRow, TeacherSkillSetRow |
| `runtime/ailine_runtime/shared/container_adapters.py` | Register SkillRepository in DI |
| `agents/ailine_agents/skills/registry.py` | Add async initialize(), optional SkillRepository |
| `runtime/ailine_runtime/api/app.py` | Call registry.initialize() in lifespan |
| `control_docs/SYSTEM_DESIGN.md` | Document skills DB schema and data flows |
