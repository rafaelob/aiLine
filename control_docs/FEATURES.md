# Features

## Done (F-001 → F-073: Sprints 0-12)
Core platform: Hexagonal arch, 3 LLM adapters, LangGraph, SmartRouter, 4 Pydantic AI agents, FastAPI+SSE, pgvector, RAG, curriculum alignment, Next.js 16 (9 WCAG themes, 3 locales), accessibility, security, Docker Compose, CI/CD. 73 features.

### Sprint 13 — Final Polish & Wow Factor (Feb 13)
F-074→F-099: Agent Trace Viewer, SmartRouter Rationale, QualityGate Hard Constraints, RAG Quoting, Observability Dashboard, Standards Alignment, Theme Morphing, Magic Tabs, Skeleton Shimmer, Staggered Entrance, Bento Grid, Typewriter SSE, Toast, Empty States, Webcam Ring, Export Fold, Degradation Panel, Privacy Panel, Cognitive Load Meter, Trace UI, Rationale Card UI, Observability UI, Error Boundary, i18n Coverage, E2E Golden Paths, Judge Artifacts (26 features).

### Sprint 14 — State-of-the-Art Hardening (Feb 13, 2026)
- [F-100] JWT RS256/ES256 Verification — Full asymmetric JWT with JWKS support, algorithm pinning, iss/aud/exp/nbf validation
- [F-101] JWT Security Test Suite — 57 tests: forged tokens, expired, wrong aud/kid, replay, tenant impersonation
- [F-102] Prompt Injection Defenses — Document trust scoring, retrieval sanitization, instruction hierarchy in RAG
- [F-103] Structured Audit Logging — Admin actions, content access, auth events to structured log
- [F-104] OpenTelemetry Tracing — Spans for FastAPI/SQLAlchemy/LLM/pipeline/tool calls, OTLP export
- [F-105] RFC 7807 Problem Details — Unified error handler, application/problem+json, field-level validation errors
- [F-106] DB Pool Tuning — pool_size=10 + max_overflow=10 for SSE workload, HNSW m=16/ef_construction=128
- [F-107] Cache Headers — Curriculum API 1h cache (static standards data)
- [F-108] Container Refactoring — container.py 476→278 LOC split into core + adapters
- [F-109] Agent Eval Harness — 15 golden test sets (5 Planner + 5 QualityGate + 5 Tutor) with rubric scoring
- [F-110] Eval Rubric System — Multi-dimension scoring (accuracy/safety/pedagogy/structure), regression detection
- [F-111] RAG Provenance Diagnostics — RetrievalResult with confidence classification, RAGDiagnostics with answerability
- [F-112] RAG Diagnostics API — GET /rag/diagnostics/{run_id} + /recent with chunk provenance
- [F-113] Sign Language Worker Fix — MediaPipe feature-gated loading, TODO stubs replaced
- [F-114] Playwright webServer Config — Self-contained E2E (build + start + test)
- [F-115] Visual Regression Tests — 8 screenshot comparisons for key layouts
- [F-116] View Transitions API — CSS-based route morphing animations
- [F-117] Dynamic OG Images — next/og ImageResponse for shared lesson links
- [F-118] PWA Manifest — manifest.json, beforeinstallprompt, icons, shortcuts, service worker registrar
- [F-119] Recharts Keyboard Accessibility — Tab through data points, aria-live announcements
- [F-120] Optimistic UI — useOptimistic hook for quick interactions

### Sprint 16 — Hackathon Victory Sprint (Feb 14, 2026)
- [F-121] Transformation Scorecard — 9-metric trust card (reading level, standards, a11y, RAG, quality, model, router, timing, exports) computed as LangGraph terminal node
- [F-122] HITL Teacher Review Panel — approve/reject/revision workflow for AI-generated plans with notes + pending reviews badge
- [F-123] Student Progress Dashboard — mastery tracking (developing/proficient/mastered), standards heatmap, class overview, record form
- [F-124] UX Micro-Polish — 8 nav items (sidebar + mobile), "Powered by Claude Opus 4.6" badge, empty state + skeleton components, teacher-friendly labels
- [F-125] Conversation Review — scrollable tutor transcript with per-turn flagging for teacher oversight

### Sprint 17 — Hackathon Final Push (Feb 15, 2026)
- [F-126] Settings Page — AI model display, language, accessibility preferences link, about info with glass morphism
- [F-127] Guided Demo Mode — URL param `?demo=true`, auto-fill wizard, floating tooltip overlay, Zustand demo-store with 3 guided steps
- [F-128] Trust & Transparency Panel — Consolidated quality report, scorecard metrics, model provenance, teacher decision badge in plan tabs
- [F-129] Materials Upload Page — File upload form, material listing with tags, glass card grid, server+client component split
- [F-130] Live Dashboard Stats — Wired to `/traces/recent` + `/progress/dashboard` APIs, plan history cards, loading skeleton
- [F-131] Tutor Persistence & Review — Zustand persist middleware for chat sessions, ConversationReview tab in tutors page
- [F-132] System Status Indicator — TopBar health check badge (green/red dot), dropdown with API/model/privacy info
- [F-133] Ruff Lint Zero — Fixed 9 RUF009 (dataclass default mutable) + 2 UP038 (isinstance union syntax) in runtime
- [F-134] Orphan Component Integration — Wired CognitiveLoadMeter, DegradationPanel, PersonaHUD, PrivacyPanel into their pages
- [F-135] Dead Code Cleanup — Removed 5 duplicate/unused components (ui/empty-state, interactive-card, stagger-list, landing/*)

### Sprint 18 — Impact Sweep & State-of-the-Art Polish (Feb 15, 2026)
- [F-136] View Transition Theme Morphing — Circular clip-path reveal animation from click origin on persona/theme switch, CSS-driven with `--vt-x`/`--vt-y` coordinates
- [F-137] Loading Skeletons for All Pages — 8 `loading.tsx` files (dashboard, plans, tutors, materials, settings, exports, observability, sign-language) with page-specific skeleton layouts
- [F-138] Mobile Nav Overflow Menu — "More" popover with 4 overflow items (materials, sign-language, observability, settings), AnimatePresence animation, Escape/click-outside close
- [F-139] HITL API Test Coverage — 51 new tests: Progress API (16), Plan Review API (18), Tutor Transcript/Flag API (17), covering success/404/422/401/403 paths
- [F-140] PreferencesPanel View Transition — Theme switch in preferences panel now uses View Transitions API for smooth circular reveal

### Sprint 19 — State-of-the-Art Final Sweep (Feb 15, 2026)
- [F-141] Command Palette (Cmd+K) — Fuzzy search, navigation (9 pages), quick actions, theme switching (9 personas), language switching (3 locales), ARIA combobox, glass morphism overlay, keyboard navigation
- [F-142] Plan Nodes Refactor — Split 764 LOC `_plan_nodes.py` into 5 focused modules (_node_shared, _planner_node, _quality_node, _executor_node, _scorecard_node) with backward-compatible barrel re-export
- [F-143] Plan Generation Flow Refactor — Split 757 LOC `plan-generation-flow.tsx` into orchestrator (379 LOC) + wizard-steps (358 LOC) + plan-result-display (104 LOC)
- [F-144] Shared Motion Variants — Extracted `containerVariants`/`itemVariants` from 9 components into `lib/motion-variants.ts`, eliminating duplication
- [F-145] SSE Type Safety — Replaced 3 `as never` casts in `use-pipeline-sse.ts` with proper `StudyPlan`, `ScorecardData`, `QualityReport` type assertions

### Sprint 20 — Maturity & Polish (Feb 15, 2026)
- [F-146] Public Landing Page — Full-screen hero with mesh gradient, animated counters, feature cards, floating glass nav, "Built with Claude Opus 4.6" footer
- [F-147] Route Group Split — `(app)/` for authenticated pages with sidebar/topbar, landing at root without app shell
- [F-148] ESLint Zero Warnings — Cleaned all 327 warnings (unused vars in test mocks) via config + targeted fixes
- [F-149] Dashboard Refactor — Extracted dashboard-icons.tsx (78 LOC), plan-history-card.tsx (66 LOC) from 541→362 LOC main file
- [F-150] Shared AnimatedCounter — Deduped spring count-up from dashboard + landing into shared component (80 LOC)
- [F-151] Landing A11y Hardening — Focus rings, aria-live counters, Next.js Link for client nav, proper heading hierarchy, reduced-motion support
- [F-152] Landing UX Polish — Gradient text animation, scroll-triggered entrances, hover card effects, responsive breakpoints
- [F-153] Landing Test Coverage — 86 new tests across 9 files (landing components, shared counter, extracted dashboard modules)
- [F-154] Security Review — 0 critical/high findings; verified ThemeScript safety, route auth boundaries, no XSS vectors
- [F-155] Repo Cleanup — .gitignore for screenshots, removed nul artifact, cleaned root-level PNGs

### Final Audit — Agent Skills & Accessibility Enhancement (Feb 15, 2026)
- [F-156] Sign Language Interpreter Skill — Libras/ASL gloss translation with grammar reference, non-manual markers, classifiers, educational vocabulary
- [F-157] Multi-Language Content Adapter Skill — Cross-language educational content adaptation with curriculum mapping (BNCC↔Common Core), cultural context, accessibility preservation
- [F-158] Progress Analyzer Skill — Learning analytics with trend detection, risk identification, intervention recommendations, flexible grouping strategies
- [F-159] Differentiated Instruction Skill — UDL-based mixed-ability planning with tiered activities, choice boards, multi-modal learning paths
- [F-160] Audio Description Generator Skill — Alt text + extended descriptions + audio scripts for visual educational content (WCAG 2.2 compliant)
- [F-161] Parent Report Generator Skill — Parent-friendly progress reports in PT-BR/EN/ES with home activity suggestions, jargon-free language
- [F-162] Skills Enhancement — All 17 skills upgraded to agentskills.io v1 spec with license, compatibility, references/ directories, detailed domain knowledge

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

## Backlog
- [F-035] Sign Language Post-MVP Path — SPOTER transformer + VLibrasBD NMT dataset (ADR-047)
- [F-163] RBAC System — Admin, student, coordinator roles with permission matrix
- [F-175] Skills DB Persistence — SQLAlchemy models (Skill, SkillVersion, TeacherSkillSet) with pgvector embeddings for skill matching
- [F-176] Skills API Endpoints — CRUD, fork, rate, suggest, craft endpoints under /v1/skills with tenant isolation
- [F-177] Skills Workflow Integration — skills_node in plan_workflow and tutor_workflow for dynamic skill resolution
- [F-178] Teacher Skill Sets — Per-teacher skill configurations with presets (e.g., "math_grade_5", "accessibility_high_support")
- [F-165] TTS Integration — ElevenLabs adapter for text-to-speech accessibility
- [F-166] Braille Export Pipeline — BRF format generation for visual impairment support
