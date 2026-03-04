# Features

## Done (F-001 → F-073: Sprints 0-12)
Core platform: Hexagonal arch, 3 LLM adapters, LangGraph, SmartRouter, 4 Pydantic AI agents, FastAPI+SSE, pgvector, RAG, curriculum alignment, Next.js 16 (9 WCAG themes, 3 locales), accessibility, security, Docker Compose, CI/CD. 73 features.

### Sprint 13 — Final Polish & Wow Factor (Feb 13)
F-074 to F-099 (26 features): Agent Trace Viewer, SmartRouter Rationale, QualityGate Hard Constraints, RAG Quoting, Observability Dashboard, Theme Morphing, Skeleton Shimmer, Typewriter SSE, Toast, Empty States, Webcam Ring, Error Boundary, i18n Coverage, E2E Golden Paths, Judge Artifacts.

### Sprint 14 — State-of-the-Art Hardening (Feb 13)
F-100 to F-120 (21 features): JWT RS256/ES256 (F-100-101), Prompt Injection Defenses (F-102), Audit Logging (F-103), OpenTelemetry (F-104), RFC 7807 Errors (F-105), DB Pool Tuning (F-106), Cache Headers (F-107), Container Refactor (F-108), Agent Eval Harness (F-109-110), RAG Provenance (F-111-112), Sign Lang Worker Fix (F-113), Playwright Config (F-114), Visual Regression (F-115), View Transitions (F-116), OG Images (F-117), PWA (F-118), Recharts A11y (F-119), Optimistic UI (F-120).

### Sprints 16-20 — Hackathon Victory through Maturity (Feb 14-15)
F-121 to F-155 (35 features): Scorecard (F-121), HITL Review (F-122), Progress Dashboard (F-123), Conversation Review (F-125), Settings (F-126), Demo Mode (F-127), Trust Panel (F-128), Materials (F-129), Dashboard Stats (F-130), Tutor Persist (F-131), Status Indicator (F-132), Lint Zero (F-133-135), View Transition Morphing (F-136), Loading Skeletons (F-137), Mobile Nav (F-138), API Tests (F-139), Command Palette (F-141), Plan Nodes Refactor (F-142), Plan Flow Refactor (F-143), Motion Variants (F-144), SSE Type Safety (F-145), Landing Page (F-146-155).

### Agent Skills Audit (Feb 15)
F-156 to F-162 (7 features): Sign Language Interpreter Skill, Multi-Language Adapter, Progress Analyzer, Differentiated Instruction, Audio Description Generator, Parent Report Generator, 17 Skills agentskills.io v1 spec upgrade.

### Sprint 21 — Skills Runtime System (Feb 15, 2026)
- [F-167] Skills Spec Validator — agentskills.io-compliant validation (slug rules, metadata string-only, token budget, frontmatter keys)
- [F-168] Accessibility Skill Policy — Deterministic mapping of 7 accessibility profiles (TEA/TDAH/learning/hearing/visual/speech_language/motor) to 17 skills with must/should/nice tiers and human review triggers
- [F-169] Skill Prompt Composer — Token-budgeted system prompt composition with priority sorting, soft caps, proportional truncation, and graceful degradation
- [F-170] SkillCrafter Agent — Pydantic AI agent for conversational skill creation by teachers, multi-turn with CraftedSkillOutput structured output
- [F-171] Dynamic Skill Loading — SkillRequestContext in AgentDeps for per-request skill selection, replacing hardcoded skill lists
- [F-172] Skills Runtime State — RunState and TutorGraphState extended with skill_request, activated_skills, skill_prompt_fragment fields
- [F-173] All 17 Skills Spec-Compliant — metadata string-only, no lists/objects, skills/ synced to .claude/skills/
- [F-174] Docker CORS Localhost — CORS origins include both localhost and 127.0.0.1 for all development ports

### Sprint 22 — Security Hardening & Expert Review (Feb 16, 2026)
- [F-179] Plan Review Tenant Isolation — Fixed IDOR: POST/GET /plans/{id}/review now enforce ownership check (403 on cross-tenant access)
- [F-180] API Schema Cleanup — Removed misleading teacher_id from MaterialIn and TutorCreateIn request bodies (auth context only)
- [F-181] Scorecard Resilience — Scorecard node now emits STAGE_FAILED SSE event and returns structured fallback instead of silent None
- [F-182] SSE Queue Hardening — stream_writer wrapped in try/except for QueueFull to prevent pipeline crash under backpressure
- [F-183] CORS Method Expansion — Added PUT/PATCH/DELETE/OPTIONS to allow_methods for full REST surface
- [F-184] Skills Registry Thread Safety — Replaced function-attribute cache with functools.lru_cache(maxsize=1) for ASGI safety
- [F-185] Settings Singleton Thread Safety — Double-checked locking with threading.Lock for get_settings()
- [F-186] CircuitBreaker Timing Fix — Increased cooldown in tests from 0.01s to 0.5s to prevent flaky failures on Windows
- [F-187] Skills Discovery API — 4 endpoints: GET /skills (list+search+filter), GET /skills/{slug} (detail), GET /skills/policy/{profile}, GET /skills/policies
- [F-188] AI Receipt SSE Event — Scorecard node emits trust chain summary (model, quality, citations, accommodations) for frontend transparency panel
- [F-189] Streaming Thought UI — Collapsible AI "thinking" panel with pulsing indicators, staggered animations, aria-live for screen readers
- [F-190] Confetti Celebration Hook — Dynamic-import canvas-confetti with reduced-motion respect and AiLine brand colors

### Sprint 23 — Landing Overhaul, Demo System, Image Gen (Feb 16, 2026)
- [F-191] Landing Page Hero with Persona Toggle — Interactive hero section with live persona switching for accessibility demonstration
- [F-192] "How It Works" 4-Step Section — Visual walkthrough: Upload -> AI Plan -> Adapt -> Track Progress
- [F-193] Demo Login System — 6 pre-built profiles (teacher, 4 students with ASD/ADHD/Dyslexia/Hearing, parent) for instant demo access
- [F-194] Demo Seed Data & Scenarios — Pre-populated courses, plans, progress records, and tutor sessions for each demo persona
- [F-195] Gemini Imagen 4 Integration — ImageGenerator port, GeminiImageGenerator adapter, POST /media/generate-image endpoint for AI image creation
- [F-196] SSE Double-Finalize Fix — Post-completion side-effects wrapped in nested try/except to prevent stream corruption
- [F-197] IDOR Surface Elimination — Removed dead teacher_id from PlanGenerateIn/PlanStreamIn request schemas (auth context only)
- [F-198] Teacher Card UX — "Start Here" badge on teacher demo card, route prefetch on hover/focus for instant navigation
- [F-199] Default Locale to English — Changed default locale from pt-BR to en for hackathon judges
- [F-200] i18n Expansion — 40+ new translation keys across all 3 locales (en, pt-BR, es) for demo system and landing page

### Sprint 24 — International Sign Languages & RBAC Login (Feb 18, 2026)
- [F-201] International Sign Language Registry — 8 sign languages (ASL, BSL, LGP, DGS, LSF, LSE, Libras, ISL) with per-language metadata, 8 common gestures each, locale mapping
- [F-202] Gloss Translator Internationalization — 8 language-specific LLM system prompts for sign-to-spoken translation (ASL→EN, DGS→DE, LSE→ES, LGP→PT, etc.)
- [F-203] Sign Language Discovery API — 4 new endpoints: GET /sign-language/languages, /languages/{code}, /languages/{code}/gestures, /for-locale/{locale}
- [F-204] WebSocket Language Selection — /ws/libras-caption now accepts ?lang= query param for international sign language selection
- [F-205] RBAC Domain Entities — UserRole(StrEnum) with 5 roles, Organization, User, StudentProfile domain models
- [F-206] RBAC ORM Models — 5 new tables: organizations, users, student_profiles, teacher_students, parent_students with UUID v7 PKs
- [F-207] RBAC Alembic Migration — Migration 0003: creates 5 RBAC tables with proper FKs and indexes
- [F-208] RBAC Middleware Integration — TenantContext extended with role + org_id contextvars, JWT claims extraction for role/org_id, dev header support (X-User-Role, X-Org-ID)
- [F-209] RBAC Authorization Module — require_role(), require_admin(), require_teacher_or_admin(), can_access_student_data() with super_admin bypass
- [F-210] Auth API Router — 4 endpoints: POST /auth/login (JWT), POST /auth/register, GET /auth/me, GET /auth/roles with in-memory store
- [F-211] Demo Admin Profiles — 2 new admin demo profiles: admin-principal (school_admin), admin-super (super_admin), total 8 profiles
- [F-212] Auth Path Exclusion Fix — Middleware changed from prefix /auth exclusion to exact-match /auth/login, /auth/register, /auth/roles so /auth/me works with auth
- [F-213] Frontend Auth Store — Zustand persist store with JWT + user profile, login/logout/updateUser actions
- [F-214] Frontend Login Page — Role-based login with 5 glass cards, demo profile selection per role, email/password form, i18n (27 keys × 3 locales)
- [F-215] Frontend Sign Language Selector — Dropdown component with 8 languages, full ARIA combobox, keyboard navigation, flag + metadata display
- [F-216] Frontend Auth Headers Priority — getAuthHeaders() now checks auth store JWT first, with graceful fallback chain

### Sprint 25 — Skills DB + Braille Phase 1 (Feb 18, 2026)
- [F-175] Skills DB Persistence — Skill/SkillVersion/SkillRating/TeacherSkillSet models, pgvector embeddings (1536d HNSW), migration 0004, SkillRepository port+adapter, 50 tests
- [F-166] Braille Phase 1 — BrfTranslator Grade 1, NABCC mapping, EN/PT-BR/ES, 40-cell wrap, pagination, 40 tests

### Sprint 26 — "Make the Invisible Visible" (Feb 19, 2026)
- [F-176] Skills API Wired — 9 endpoints under /v1/skills wired to app factory with SessionFactorySkillRepository, CRUD + fork + rate + suggest
- [F-177] Skills Workflow Integration — skills_node in plan_workflow + tutor_workflow with DB-backed resolution, SSE stage events
- [F-165] TTS Integration — ElevenLabs adapter wired, POST /media/tts/synthesize + GET /voices, FakeTTS fallback
- [F-217] Agent Pipeline Visualization — 6-node real-time CSS Grid graph (RAG, Profile, Planner "Opus 4.6", QualityGate, Executor, Export), SSE-driven state transitions, motion animations
- [F-218] Adaptation Diff View — Split-pane standard vs AI-adapted curriculum with profile tabs (ASD/ADHD/Dyslexia/Hearing), diff highlighting (additions/modifications/removals)
- [F-219] Evidence Panel — 6-section trust accordion (AI Model, Quality Score gauge, Standards Aligned, RAG Provenance bar, Accommodations, Processing Time), ai_receipt SSE integration
- [F-220] TTS Audio Player — Play/pause, speed selector (0.5x-2x), language/voice selectors, progress bar, API integration
- [F-221] Braille Download + Copy — Download .brf file + copy to clipboard buttons added to BraillePreview component
- [F-222] Inclusive Classroom Mode — "One Lesson, Four Adapted Plans" 2x2 teacher cockpit grid (Lucas/ASD, Sofia/ADHD, Pedro/Dyslexia, Ana/Hearing) with accent colors and accommodation badges

### Improvements Branch — Comprehensive Review & Polish (Feb 19, 2026)
- [F-223] A11y Status Badge — Floating "Make the Invisible Visible" indicator showing active persona + features count, expandable detail panel, ARIA-compliant (11 tests)
- [F-224] Persona Explainer Banner — "Why this adaptation?" context banner below topbar, shows persona icon/name/hints, aria-live polite (8 tests)
- [F-225] Capabilities Endpoint — GET /capabilities returns platform feature availability (LLM, TTS, image gen, vector search, braille, skills, demo mode), excluded from auth/rate-limit (3 tests)
- [F-226] Enhanced Focus States — WCAG-compliant outline+offset focus indicators, forced-colors mode support for Windows High Contrast
- [F-227] Theme Color Preview Chips — 3 color circles (bg, primary, text) next to each theme in preferences panel
- [F-228] Config Validation at Startup — Settings.validate_environment() called before Container.build(), fail-fast with structured warnings
- [F-229] Comprehensive Test Expansion — 16 new test files, 133 new tests covering login phases, auth store, sign language selector, wizard steps, settings, API, demo data

### Sprint 27 — Production-Grade Polish (Feb 20, 2026)
- [F-230] PostgresUserRepository — SessionFactoryUserRepository with DI wiring for persistent user storage
- [F-231] JWT Hardening — RS256/HS256 algorithm selection, jti claim + Redis blacklist, POST /auth/logout, configurable TTL
- [F-232] Health Diagnostics Split — public /health/diagnostics vs private /internal/diagnostics with auth
- [F-233] Before/After Accessibility Compare Slider — draggable theme comparison, keyboard accessible
- [F-234] Pipeline Edge Animations — SVG stroke-dashoffset flow + node glow states
- [F-235] Motor Accessibility Mode — MotorStickyToolbar with 56px targets, pill shapes, focus halos
- [F-236] Micro-interactions — btn-press scale(0.97), slide-in animation, dash-flow keyframe
- [F-237] Run Resource Model — GET /runs (list + filter + pagination), GET /runs/{id} (detail)
- [F-238] RFC 7807 Error Model — already implemented (error_handler.py, application/problem+json)
- [F-239] TenantContext Explicit Dependencies — all routers use Depends(require_authenticated)
- [F-240] Config Deduplication — AiLineConfig deprecated with DeprecationWarning, Settings is canonical
- [F-241] Cache Skill Registry — _get_skills_info() cached once, used by diagnostics + capabilities
- [F-242] Demo Storyboard — 2 tracks (Teacher/Accessibility), 5 steps each, full i18n
- [F-243] Demo Profile Key Mismatch — VALID_DEMO_PROFILES includes both short and long keys
- [F-244] EvidencePanel aria-labelledby Fix — missing id on toggle button
- [F-245] PreferencesPanel Focus Restore — stale closure fix
- [F-246] JWT iss/aud Claims — mint when env vars configured
- [F-247] /auth/demo-login Endpoint — proper JWT flow with short/long key aliases
- [F-248] Demo Users Seeded — hashed password (demo123), email login works
- [F-249] Login Rate Limit — raised to 20/min for demo-friendly Docker testing
- [F-250] Docker Frontend Memory — 512M to 2G, NODE_OPTIONS=--max-old-space-size=1536

### Sprint 28 — Security Containment + Docs Sync (Feb 21, 2026)
- [F-251] Demo Login Privilege Escalation Fix — _validate_role() enforcement + admin profiles removed from DEMO_PROFILES
- [F-252] TraceStore Tenant Integrity — append_node/update_run no longer auto-create RunTrace
- [F-253] Dev Mode Default OFF — AILINE_DEV_MODE defaults to false in Docker Compose
- [F-254] JWT Dev Secret Module — Shared jwt_dev_secret.py replaces hardcoded fallback secrets
- [F-255] Demo Login Rate Limiting — Per-IP rate limit (20/min) on /auth/demo-login
- [F-256] Diagnostics Admin-Only — /internal/diagnostics restricted to admin role
- [F-257] Rate Limiter Docs Alignment — Docstrings corrected to 20 attempts/minute
- [F-258] Redis Access Encapsulation — EventBus.get_redis_client() protocol method replaces private _redis
- [F-259] TraceStore Server-Side Filtering — list_recent() accepts status parameter
- [F-260] Seed Import Unification — All imports use demo_profiles module directly
- [F-261] Role Validation 422 — _validate_role() raises HTTP 422 for invalid roles
- [F-262] Body Immutability — plans_stream uses Pydantic model_copy instead of mutation
- [F-263] SessionStorage JWT Cleanup — Removed insecure sessionStorage fallback
- [F-264] Docker Port Hardening — DB/Redis ports bound to 127.0.0.1
- [F-265] SYSTEM_DESIGN.md Version Sync — Tailwind, motion, next-intl, pydantic-ai versions corrected
- [F-266] FEATURES.md Sprint 27 — Added Sprint 27 section (F-230 to F-250)
- [F-267] SECURITY.md Roles Update — Corrected to 5 roles (super_admin through parent)
- [F-268] RUN_DEPLOY.md Port Defaults — Fixed port defaults (8011/3011/5411/6311)
- [F-269] TEST.md Counts Update — Updated to ~3,889 tests, fixed pytest command
- [F-270] Frontend CLAUDE.md Sync — Tailwind and motion versions corrected
- [F-271] I18N Diacritics Fix — 7 pt-BR + 1 es diacritics corrected

## Planned — Sprint 29: Design System, SVG Illustrations, Core Views & Emotional UX ("Soft Clay")
F-272→F-310 (39 stories, 6 phases, 3 weeks). HIGHEST PRIORITY. Design: "Soft Clay 2.5D Organic" via Gemini-3.1-Pro (6 consultations). Benchmarks: Khan Academy, Duolingo, Seesaw, Google Classroom. Phase 1: design system (tokens, tailwind-variants, lucide-react, Inter+Jakarta Sans, Azure/Sage/Amber). Phase 2: SVG illustration system (38+ Gemini-generated SVGs — empty states, onboarding, landing, personas, a11y icons). Phase 3: 3 CRITICAL missing views (Learning Analytics Dashboard, Student Learning View, Parent Progress Report + Recharts a11y infra). Phase 4: page redesigns (landing, dashboard, tablet, dark theme, onboarding). Phase 5: emotional safety (neutral errors, visual timer, Quiet Mode, ADHD support, Dyslexia rows). Phase 6: engagement (drag-and-drop, PWA, Learning Rhythm gamification). Stretch: Constellation map, push notifications, multimodal responses, Transition Passport.

## Planned — Sprint 30: Backend Production, Observability & Compliance
F-311→F-330 (20 stories, 6 phases, 2-3 weeks). Architecture: GPT-5.3-codex (3 consultations). GDPR/LGPD verified. Phase 1 (Day 1): GEMINI_API_KEY fix (config.py AliasChoices), PII log redaction, Google paid-service guard. Phase 2: audit log + PII encryption. Phase 3: OTEL Redis, trace-ID correlation, LLM baggage. Phase 4: distributed idempotency, SmartRouter failover, SSE backpressure, graceful shutdown, K8s probes. Phase 5: split app.py/auth.py/models.py + remove AiLineConfig. Phase 6: Docker CI + Playwright CI.

## Planned — Sprint 31: Architecture Evolution & Agent Maturity
F-331→F-345 (15 stories, 4 phases, 2-3 weeks). Phase 1: service layer (Commands/Queries), domain events, arq worker. Phase 2: API versioning (/v1/), cursor pagination. Phase 3: prompt registry, per-tenant cost tracking, content safety guardrails, semantic AI caching. Phase 4: persistent stores, embedding fix, InMemoryStore base, PgVectorStore cleanup, global state docs.

## Planned — Sprint 32A: Privacy Compliance (LGPD/GDPR)
F-346→F-355 (10 stories, 2 weeks). Data tier classification, portability export (LGPD Art.18), deletion/anonymization pipeline, minor consent (LGPD Art.14), retention engine, incident response (ANPD 3d/GDPR 72h), provider DPA register, Redis eviction safety, Postgres RLS, notification service.

## Planned — Sprint 33+: Advanced Features
F-356→F-375 (20 stories, 4-6 weeks). Gamification: Learning Rhythm, Skill Nodes, Constellation. Educational intelligence: spaced repetition, IEP tracking, AI Social Stories (ASD), predictive accommodations, cognitive simplification. Platform: feature flags, CQRS, A/B testing, personalization engine. Infra: Meilisearch, API SDK generation, admin dashboard, batch operations, webhooks, Git LFS, AT testing.

## Planned — Sprint 34: Emotional Safety & Executive Function (Empowerment Pillar 1)
F-376→F-393 (18 stories, 4 phases, 3 weeks). SAMHSA 6 Trauma-Informed Principles + 6-subsystem Executive Function Support. Architecture: Gemini-3.1-Pro (3 consultation rounds). Phase 1 (P0): transition warnings ASD (aria-live="assertive"), task decomposition "Stepping Stones" SVG, safe feedback (amber not red, no "wrong" language), global undo + auto-save. Phase 2 (P0): working memory "Where was I?", initiation support "Just Start", emotional check-in (energy/pleasantness grid), frustration detection + de-escalation, breathing exercise, parking lot (distracting thoughts). Phase 3 (P1): productive struggle indicator, dignity-preserving celebrations (per-persona: TEA=text-only), self-assessment emoji scale. Phase 4 (P2): asset-based parent reports (no deficit language), growth portfolio, store integration, i18n 40+ keys, test suite. New: 12 DB tables, 15 API endpoints, 7 Zustand stores, CSS token changes (--color-feedback-safe).

## Planned — Sprint 35: AI Educational Intelligence Tools (Empowerment Pillar 2)
F-394→F-411 (18 stories, 3 phases, 3 weeks). 3 AI-powered tools closing accommodation→empowerment gap. Architecture: Gemini-3.1-Pro (3 rounds). Phase 1 (P0): SocialStoryAgent (Carol Gray 10.2 methodology, deterministic 4:1 ratio validation, 10 scenario templates, multi-format export: text/audio/PDF/cards, StoryCardViewer). Phase 2 (P0-P1): readability analysis (Flesch-Kincaid/Gunning Fog deterministic), 4-level SimplificationAgent (Original→Simplified→Highly Simplified→Symbol-Supported), ComplexitySlider UI, plan_workflow/tutor_workflow integration. Phase 3 (P1): telemetry ingestion (7 signal types, partitioned, Redis buffer), BehavioralAnalyzer (rolling windows, 0-1 normalized), AccommodationPredictor (heuristic rules, dignity framing, NEVER auto-activate), ZPD adaptive difficulty (Vygotsky, frustration ceiling), teacher insights dashboard. New: 2 Pydantic AI agents, 3 skills, 1 LangGraph workflow, 5 DB tables, 14 API endpoints.

## Planned — Sprint 36: IEP/MTSS, SM-2 Spaced Repetition, Mastery & Personalization (Empowerment Pillar 3)
F-412→F-447 (36 stories, 5 phases, 4-6 weeks). Educational data intelligence backbone. Architecture: GPT-5.3-codex (2 rounds) + GPT-5.2 thinkdeep. Phase 1 (P0): IEP document lifecycle (7 states), SMART goals (curriculum-linked), 6 accommodation categories, progress monitoring (4 evidence types), services tracking, team/notifications, domain entities + repository. Phase 2 (P0): MTSS 3-tier system, evidence-based intervention catalog (4 evidence levels), student interventions + fidelity tracking, screening + meetings, domain entities. Phase 3 (P0): consent management (IDEA + LGPD Art. 14, 6 consent types), immutable audit ledger (SHA-256 hashes), data retention policies (IEP 7yr, MTSS 5yr, reviews 3yr). Phase 4 (P1): review items (7 modalities), student review profiles (processing speed matrix: 7 needs × 7 modalities), SM-2 inclusive adaptation (calibration period, streak bonus, PSF), fatigue detection (3 rules), due reviews, review sessions, health dashboard, tutor integration (review_check_node). Phase 5 (P1-P2): mastery map (5 levels, ZPD bounds), evidence collection (5 sources), skill gap analysis, learning profiles, AI recommendations engine (heuristic-first, teacher approval), auto-generation from mastery, data retention enforcement, privacy dashboard. New: 24 DB tables, 38 API endpoints, 6 domain entity files, 6 repository ports + adapters, migration 0006.

## Backlog
- [F-035] Sign Language Post-MVP — SPOTER transformer + VLibrasBD NMT
- [F-178] Teacher Skill Sets — per-teacher presets
- Braille Grade 2 via liblouis
- Symbol-Supported Text (PCS pictograms)
- Synchronized word-level TTS highlighting
- Haptic/Vibrational feedback (Web Haptics API)
