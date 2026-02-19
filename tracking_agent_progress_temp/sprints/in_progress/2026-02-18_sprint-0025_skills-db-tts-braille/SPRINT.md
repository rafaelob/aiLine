# Sprint 25 — Skills DB Persistence, TTS Integration, Braille Export

**Status:** in_progress
**Start:** 2026-02-18
**End:** TBD
**Goal:** Complete the Skills vertical slice (DB persistence + API + workflow integration) and deliver two critical accessibility features (TTS + Braille export)

## Scope

### Phase 1 — Foundation (parallel tracks)

#### Track A: Skills DB Persistence (F-175) ✓ COMPLETE (Round 1)
- [x] A1: Design SQLAlchemy models: Skill, SkillVersion, TeacherSkillSet with pgvector embedding column (1536d)
- [x] A2: Create Alembic migration 0004 for skills tables (skills, skill_versions, skill_ratings, teacher_skill_sets) with HNSW index
- [x] A3: Implement SkillRepository port (Protocol) with CRUD + similarity search (12 methods)
- [x] A4: Implement PostgresSkillRepository adapter using SQLAlchemy + pgvector + FakeSkillRepository
- [ ] A5: Seed migration: load 17 filesystem skills into DB with embeddings
- [ ] A6: Add SkillRepository to DI container (container.py)
- [x] A7: Write unit tests for Skill/SkillVersion/TeacherSkillSet domain entities (50 tests)
- [x] A8: Write integration tests for PostgresSkillRepository (CRUD + vector search + fork + rate)
- [ ] A9: Update SYSTEM_DESIGN.md with skills DB schema

#### Track B: TTS Integration (F-165)
- [ ] B1: Define TTS port (Protocol): synthesize(text, voice, locale) -> AudioResult
- [ ] B2: Implement ElevenLabsTTSAdapter using ElevenLabs API (v2)
- [ ] B3: Implement FallbackTTSAdapter: ElevenLabs -> Chatterbox Turbo -> Kokoro (3-tier)
- [ ] B4: Add TTS configuration: env vars for API key, voice IDs, rate limits
- [ ] B5: Create POST /media/tts endpoint (text, locale, voice_preset, format)
- [ ] B6: Add TTS to DI container with circuit breaker wrapper
- [ ] B7: Frontend: audio player component with playback controls, speed adjustment
- [ ] B8: Frontend: "Read Aloud" button on plan results and tutor responses
- [ ] B9: Write unit tests for TTS adapters (mock external API)
- [ ] B10: Write integration test for TTS endpoint (with ElevenLabs sandbox or mock)
- [ ] B11: i18n: TTS labels for 3 locales (en, pt-BR, es)

### Phase 2 — API & Output (parallel tracks, after Phase 1)

#### Track C: Skills API Endpoints (F-176)
- [ ] C1: GET /v1/skills — list + search + filter (by tag, profile, locale) with pagination
- [ ] C2: GET /v1/skills/{slug} — detail with full instructions + metadata
- [ ] C3: POST /v1/skills — create new skill (teacher role required)
- [ ] C4: PUT /v1/skills/{slug} — update skill (owner or admin)
- [ ] C5: DELETE /v1/skills/{slug} — soft-delete (owner or admin)
- [ ] C6: POST /v1/skills/{slug}/fork — fork skill to teacher's set
- [ ] C7: POST /v1/skills/{slug}/rate — rate skill (1-5 stars)
- [ ] C8: GET /v1/skills/suggest — AI-powered skill suggestions based on context
- [ ] C9: POST /v1/skills/craft — invoke SkillCrafter agent for new skill creation
- [ ] C10: Tenant isolation: all endpoints enforce teacher_id ownership via TenantContext
- [ ] C11: Write API tests for all 9 endpoints (success + 401/403/404/422 paths)
- [ ] C12: OpenAPI schema validation for all request/response models

#### Track D: Braille Export Pipeline (F-166) — Partially Complete (Round 1)
- [ ] D1: Define BrailleExporter port (Protocol): export(plan, grade) -> BRFResult
- [x] D2: Implement Grade 1 Braille translator (ASCII -> BRF character mapping) — NABCC, EN/PT-BR/ES
- [ ] D3: Implement Grade 2 Braille contractions (common English contractions)
- [x] D4: Add BRF file generation with proper page formatting (40 cells x 25 lines)
- [ ] D5: Create POST /exports/braille endpoint (plan_id, grade, locale)
- [ ] D6: Frontend: "Export Braille" button in export viewer with grade selection
- [x] D7: Add Braille to export variants (ExportFormat.BRAILLE_BRF — 11th format)
- [x] D8: Write unit tests for Braille character mapping
- [ ] D9: Write integration test for BRF file generation
- [ ] D10: i18n: Braille export labels for 3 locales

### Phase 3 — Integration (after Phase 2)

#### Track E: Skills Workflow Integration (F-177)
- [ ] E1: Create skills_node for plan_workflow: resolve activated skills from DB based on SkillRequestContext
- [ ] E2: Create skills_node for tutor_workflow: inject skill instructions into tutor system prompt
- [ ] E3: Update LangGraph StateGraph topology: add skills_node before planner_node (plan) / respond_node (tutor)
- [ ] E4: Migrate SkillPromptComposer to use DB-backed skills instead of filesystem
- [ ] E5: Add skill activation logging to SSE events (skill.activated, skill.composed)
- [ ] E6: Frontend: show activated skills in Streaming Thought UI panel
- [ ] E7: Write integration tests for skills_node in both workflows
- [ ] E8: Write E2E test: plan generation with DB-backed skill resolution

## Acceptance Criteria

- [ ] Skills stored in PostgreSQL with pgvector embeddings; similarity search returns top-k skills
- [ ] 9 REST endpoints under /v1/skills with full RBAC (teacher creates, admin manages, student reads)
- [ ] Skills resolved from DB in plan_workflow and tutor_workflow via skills_node
- [ ] TTS endpoint generates audio for plan text and tutor responses (3 locales)
- [ ] Braille export generates valid BRF files (Grade 1 + Grade 2)
- [ ] All existing 3,548 tests still pass
- [ ] 155+ new tests for skills DB, skills API, TTS, Braille, workflow integration
- [ ] Docker Compose 4 services healthy
- [ ] 0 lint/type errors (ruff, mypy, tsc, eslint)
- [ ] control_docs updated with new schemas, endpoints, and dependencies

## Dependencies

- PostgreSQL 16 + pgvector 0.8.1 (existing)
- ElevenLabs API key (env: ELEVENLABS_API_KEY)
- google-genai SDK for embedding generation (existing: gemini-embedding-001)
- Pydantic AI 1.58.0 for SkillCrafter integration (existing)
- LangGraph 1.0.8 for workflow node additions (existing)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| pgvector HNSW index build time with 17+ skills | Low | Skills count is small; index builds in <1s |
| ElevenLabs API rate limits | Medium | 3-tier fallback (ElevenLabs -> Chatterbox -> Kokoro); circuit breaker |
| Braille Grade 2 contraction complexity | Medium | Start with Grade 1 (full support); Grade 2 as best-effort |
| Skills workflow node adds latency to plan generation | Medium | Async prefetch; cache activated skills per session |
| Migration 0004 conflicts with existing schema | Low | Test migration on fresh + existing DB; rollback script |

## Test Plan

| Area | Tests | Type |
|------|-------|------|
| Skill/SkillVersion/TeacherSkillSet entities | 20 | Unit |
| PostgresSkillRepository CRUD + vector search | 15 | Integration |
| Skills API (9 endpoints x success/error) | 30 | Integration |
| TTS adapters + endpoint | 15 | Unit + Integration |
| Braille translator + BRF generation | 15 | Unit |
| Braille export endpoint | 5 | Integration |
| skills_node in plan_workflow | 10 | Integration |
| skills_node in tutor_workflow | 10 | Integration |
| E2E: plan with DB skills + TTS + Braille export | 5 | E2E |
| Frontend: audio player, braille button, skill display | 30 | Vitest |
| **Total** | **155+** | |

## Decisions

- F-178 (Teacher Skill Sets) deferred to Sprint 26 — dependency on F-175/F-176 completion
- Skills API uses /v1/skills prefix (versioned) to avoid conflicts with existing /skills discovery API
- TTS uses 3-tier fallback architecture designed in Sprint 9 (now implemented)
- Braille starts with English; Portuguese/Spanish Braille tables added in Sprint 26
- Consensus: hybrid approach (Skills + Accessibility in parallel) per GPT-5.2/Gemini-3-Pro debate

## Round 2 Progress (mega-review-r2 team)

| Agent | Task | Status |
|-------|------|--------|
| test-verifier | Rebuild Docker, run ALL tests, verify R1 fixes | in_progress |
| skills-api | Implement Skills API F-176 (9 endpoints) | in_progress |
| tts-implementer | Implement TTS ElevenLabs adapter F-165 | in_progress |
| a11y-verifier | Full WCAG 2.2 AA audit + Braille frontend | in_progress |
| expert-reviewer | GPT-5.2 + Gemini-3-Pro expert debate | in_progress |
| *(blocked)* | Skills workflow F-177 + Sprint closeout | pending (blocked by #1, #2) |

## Sprint 26 Preview (Deferred)

- F-178: Teacher Skill Sets — per-teacher presets with CRUD UI
- Braille i18n: Portuguese + Spanish Braille tables
- Skills marketplace: public skill sharing between teachers
- Auth: migrate from in-memory store to PostgreSQL-backed user persistence
