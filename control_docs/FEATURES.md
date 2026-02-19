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

## Backlog
- [F-035] Sign Language Post-MVP Path — SPOTER transformer + VLibrasBD NMT dataset (ADR-047)
- [F-178] Teacher Skill Sets — Per-teacher skill configurations with presets
