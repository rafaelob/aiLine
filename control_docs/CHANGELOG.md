# Changelog
All notable changes documented here. Format: [Keep a Changelog](https://keepachangelog.com/).

## [0.12.0] - 2026-02-19 (Sprint 26 — "Make the Invisible Visible")

### Added
- Agent Pipeline Visualization — 6-node real-time CSS Grid graph showing RAG/Profile/Planner(Opus 4.6)/QualityGate/Executor/Export with SSE-driven state transitions (F-217)
- Adaptation Diff View — split-pane standard vs AI-adapted curriculum with 4 profile tabs and diff highlighting (F-218)
- Evidence Panel — 6-section trust accordion with quality gauge, RAG provenance bar, ai_receipt integration (F-219)
- TTS Audio Player — play/pause, speed/language/voice selectors, progress bar, API integration (F-220)
- Braille Download + Copy — download .brf file and copy to clipboard on BraillePreview component (F-221)
- Inclusive Classroom Mode — 2x2 teacher cockpit grid (ASD/ADHD/Dyslexia/Hearing) with accent colors and accommodation badges (F-222)
- Skills API wired to app factory with SessionFactorySkillRepository (F-176)
- TTS router wired with ElevenLabs/FakeTTS fallback and Settings field (F-165)
- Skills workflow nodes integrated in plan + tutor workflows (F-177)

### Fixed
- 15 ruff lint errors across 8 backend files (import sorting, naming, unused imports)
- 2 TypeScript errors (FeatureItem icon type union, ReactNode cast in learning-trajectory)
- ai_receipt SSE event type mismatch in evidence panel extraction
- evidence-panel null-safety for curriculum_alignment and accessibility_notes
- Docker frontend memory limit increased to 2G (prevents OOM during test suite)

### Changed
- Strategic architecture review by GPT-5.2 + Gemini-3.1-Pro: "Make the invisible visible" theme
- Total: 2,348 runtime + 277 agents + 1,236 frontend = **~3,861 tests passing**

## [0.11.0] - 2026-02-18 (Sprint 25 — Skills DB + Braille Phase 1)

### Added
- Skills DB Persistence — Skill/SkillVersion/SkillRating/TeacherSkillSet with pgvector embeddings, migration 0004, repository (F-175)
- Braille Phase 1 — BrfTranslator Grade 1, NABCC mapping, EN/PT-BR/ES, 40-cell wrap (F-166)

## [0.10.1] - 2026-02-18 (Mega Review — Security & Architecture Hardening)

### Fixed (CRITICAL)
- **C1**: Rate limiter threading.Lock replaced with asyncio.Lock — was blocking the asyncio event loop under concurrency
- **C2**: Unverified JWT decode no longer trusts role/org_id claims — hardcoded to "teacher" in dev mode to prevent super_admin forging

### Fixed (HIGH)
- **H1**: SkillRow.slug changed from globally unique to composite unique (teacher_id, slug) — allows per-tenant skill forking
- **H3**: JWT token removed from localStorage persist (XSS mitigation) — now lives in memory only via Zustand store
- **M5**: Skills node no longer emits raw exception strings via SSE — generic "skills_resolution_failed" message instead
- **M6**: isTokenExpired now treats tokens without exp claim as expired (safe default)
- **M9**: accessibility_needs input sanitized against known categories to prevent prompt injection
- **M12**: JWT success log downgraded from info to debug level (LGPD privacy)

### Added
- Super-admin cross-tenant access audit trail (structured warning log)
- 18 ruff lint errors fixed across 6 files (import sorting, unused imports/vars, code style)

### Changed
- Mega architecture review by GPT-5.2 + Gemini-3-Pro: 25 issues identified (2 critical, 5 high, 12 medium, 6 low)
- Total: 2,358 backend + 1,137 frontend = **3,495 tests passing**, 0 lint/type errors

## [0.10.0] - 2026-02-18 (International Sign Languages & RBAC Login)

### Added
- International sign language registry — 8 languages (ASL, BSL, LGP, DGS, LSF, LSE, Libras, ISL) with metadata, 8 gestures each, locale mapping (F-201)
- Sign language discovery API — 4 endpoints: languages list/detail, gestures per language, locale recommendation (F-203)
- WebSocket language selection via ?lang= query param (F-204)
- RBAC domain entities — UserRole (5 roles), Organization, User, StudentProfile (F-205)
- RBAC ORM models — 5 new tables: organizations, users, student_profiles, teacher_students, parent_students (F-206)
- RBAC Alembic migration 0003 (F-207)
- RBAC middleware integration — role + org_id contextvars, JWT claims extraction (F-208)
- Authorization module — require_role(), require_admin(), can_access_student_data() with super_admin bypass (F-209)
- Auth API router — POST /auth/login, /register, GET /me, /roles (F-210)
- 2 admin demo profiles: admin-principal (school_admin), admin-super (super_admin) (F-211)
- Frontend auth store (Zustand persist) with JWT + user profile (F-213)
- Frontend login page with role-based selection, demo profiles, email/password form, i18n (F-214)
- Sign language selector component — 8 languages, ARIA combobox, keyboard nav (F-215)
- 235 new tests (RBAC authz, sign language registry, auth endpoints, user entities)

### Fixed
- Auth middleware path exclusion — /auth/me now works with authentication (was excluded by /auth prefix) (F-212)
- Gloss translator internationalized for 8 sign languages with per-language LLM prompts (F-202)

### Changed
- Frontend auth headers priority — JWT from auth store checked first, graceful fallback chain (F-216)
- Total: 2,155 runtime + 277 agents + 1,116 frontend = **3,548 tests passing**

## [0.9.0] - 2026-02-16 (Landing Overhaul, Demo System, Image Gen)

### Added
- Demo login system — 6 pre-built profiles (teacher, 4 students with ASD/ADHD/Dyslexia/Hearing, parent) with seed data (F-193, F-194)
- Gemini Imagen 4 integration — ImageGenerator port, GeminiImageGenerator adapter, POST /media/generate-image (F-195)
- Landing page hero with persona toggle and "How It Works" 4-step section (F-191, F-192)
- "Start Here" badge on teacher card, route prefetch on hover/focus (F-198)
- i18n expansion — 40+ new keys across all 3 locales for demo system and landing (F-200)

### Fixed
- SSE double-finalize — post-completion side-effects wrapped in nested try/except (F-196)
- IDOR surface elimination — removed dead teacher_id from PlanGenerateIn/PlanStreamIn (F-197)

### Changed
- Default locale changed from pt-BR to English for hackathon judges (F-199)
- Total: 1,941 runtime + 277 agents + 1,115 frontend = **3,333 tests passing**

## [0.8.0] - 2026-02-16 (Security Hardening & Expert Review)

### Fixed
- **CRITICAL:** Cross-tenant IDOR in plan review endpoints — POST/GET now enforce ownership check (F-179)
- **HIGH:** Scorecard node silently swallowed exceptions — now emits STAGE_FAILED + structured fallback (F-181)
- **HIGH:** SSE stream_writer could crash on QueueFull — wrapped in try/except (F-182)
- Misleading teacher_id field removed from MaterialIn and TutorCreateIn request schemas (F-180)
- CircuitBreaker test flakiness on Windows (timing increased to 0.5s cooldown) (F-186)

### Added
- Skills Discovery API — 4 endpoints: list+search, detail, policy per profile, all policies (F-187)
- AI Receipt SSE event — trust chain summary for frontend transparency (F-188)
- Streaming Thought UI — collapsible thinking panel with pulsing indicators, aria-live (F-189)
- Confetti celebration hook — dynamic-import, reduced-motion respect, brand colors (F-190)

### Improved
- CORS: expanded allow_methods to include PUT/PATCH/DELETE for full REST surface (F-183)
- Skills registry: thread-safe caching via functools.lru_cache (F-184)
- Settings singleton: double-checked locking for ASGI worker safety (F-185)
- Expert review by GPT-5.2 (architecture/backend) and Gemini-3-Pro (frontend/UX)
- Total: 1,915 runtime + 287 agents + 1,064 frontend = **3,266 tests passing**

## [0.7.0] - 2026-02-15 (Skills Runtime System)

### Added
- Skills Spec Validator — agentskills.io-compliant validation (F-167)
- Accessibility Skill Policy — 7 profiles → 17 skills with must/should/nice tiers (F-168)
- Skill Prompt Composer — token-budgeted composition with priority sort (F-169)
- SkillCrafter Agent — conversational skill creation for teachers (F-170)
- Dynamic Skill Loading — SkillRequestContext in AgentDeps (F-171)
- Skills Runtime State — RunState/TutorGraphState with skill fields (F-172)
- All 17 skills agentskills.io spec-compliant (F-173)
- Docker CORS for localhost + 127.0.0.1 (F-174)

## [0.6.0] - 2026-02-15 (Maturity & Polish)
Landing page (F-146), route groups (F-147), 327 ESLint warnings fixed (F-148), dashboard refactor (F-149), AnimatedCounter (F-150), a11y hardening (F-151), UX polish (F-152), 86 new tests (F-153), security review (F-154), repo cleanup (F-155). **3,173 tests.**

## [0.5.0] - 2026-02-15 (State-of-the-Art Final Sweep)
Command Palette (F-141), plan nodes refactor (F-142), plan flow refactor (F-143), shared motion variants (F-144), SSE type safety (F-145). **3,087 tests.**

## [0.4.0] - 2026-02-15 (Impact Sweep)
View Transition morphing (F-136), loading skeletons (F-137), mobile nav overflow (F-138), 51 API tests (F-139), PreferencesPanel transitions (F-140). **3,066 tests.**

## [0.3.0] - 2026-02-15 (Hackathon Final Push)
Settings (F-126), Demo Mode (F-127), Trust Panel (F-128), Materials (F-129), Dashboard Stats (F-130), Tutor Persist (F-131), Status Indicator (F-132), lint zero (F-133-135). **3,002 tests.**

## [0.2.0] - 2026-02-14 (Hackathon Victory Sprint)
Scorecard (F-121), HITL Review (F-122), Progress Dashboard (F-123), Conversation Review (F-125). **2,900 tests.**

## [0.1.1] - 2026-02-14 (Excellence Sweep)
114 mypy -> 0, LangGraph state leak fix, server-side translations, a11y landmarks, Ruff 0.

## [0.1.0] - 2026-02-13 -- Hackathon Release (120 features, 60 ADRs, 2700+ tests)
