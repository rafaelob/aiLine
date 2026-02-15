# Features

## Done (F-001 → F-073: Sprints 0-12)
Core platform: Hexagonal arch, 3 LLM adapters, LangGraph workflows, SmartRouter, 4 Pydantic AI agents, FastAPI+SSE (14 events), SQLAlchemy+pgvector, RAG pipeline, curriculum alignment (BNCC/CCSS/NGSS+Bloom), Next.js 16 (React 19, Tailwind 4, 9 WCAG themes, 3 locales), accessibility (VLibras, MediaPipe, Whisper, TTS, OCR), wow features (Cognitive Curtain, Bionic Reading, Glass Box Viewer), security (JWT RS256/ES256, prompt injection, CSP), observability (OTel, Prometheus, circuit breaker), Docker Compose, CI/CD, 65 live API tests. 73 features total — see git history for individual entries.

### Sprint 13 — Final Polish & Wow Factor (Feb 13, 2026)
- [F-074] Agent Trace Viewer — GET /traces/{run_id}, LangGraph node execution timeline with inputs/outputs/time/tools/quality
- [F-075] SmartRouter Route Rationale — "Why this model?" payload in SSE stage.started events (task type, weighted scores, model selection reason)
- [F-076] QualityGate Hard Constraints — 4 deterministic validators (reading level, a11y adaptation, RAG citation, assessment item)
- [F-077] RAG-Grounded Quoting — 1-3 source quotes with doc title/section, confidence labels (high/medium/low)
- [F-078] Observability Judge Dashboard — GET /observability/dashboard (LLM provider, latency p50/p95, error rate, CB state, SSE counts, token usage/cost)
- [F-079] Standards Alignment Evidence — GET /observability/standards-evidence/{run_id} + teacher handout export with BNCC/CCSS/NGSS/Bloom
- [F-080] Theme Morphing Animation — CSS transition-colors 500ms on body for smooth accessibility theme switching
- [F-081] Magic Layout Tabs — Motion layoutId sliding active tab indicator
- [F-082] Skeleton Shimmer Loading — animate-pulse SkeletonCardGrid with React 19 Suspense fallbacks
- [F-083] Staggered Dashboard Entrance — Motion staggerChildren 0.12s sequential load animation
- [F-084] Bento Grid Dashboard — CSS Grid responsive layout (grid-cols-4) with semantic widget sizing
- [F-085] Streaming Typewriter Effect — Token-by-token SSE rendering with motion.div fade+slide in Tutor ChatBlock
- [F-086] Toast Notifications — sonner integration for AI action completion with undo capability
- [F-087] Interactive Empty States — text-balance typography with CTA buttons for empty lists
- [F-088] Webcam Active Ring — Confidence-based border glow on sign language recognition
- [F-089] Export Paper Fold — motion.article rotateY expand animation on Export Viewer
- [F-090] Degradation Panel — Demo-mode chaos simulation (Redis down, LLM timeout) with status banner
- [F-091] Privacy Data Panel — Data summary, retention policies, export/delete with LGPD/FERPA compliance display
- [F-092] Cognitive Load Meter — 3-factor heuristic (UI density 40%, reading level 35%, interactions 25%) with simplify suggestion
- [F-093] Agent Trace Viewer UI — Collapsible timeline component for LangGraph node visualization
- [F-094] SmartRouter Rationale Card UI — Expandable badge with 5 weight category breakdown
- [F-095] Observability Dashboard UI — Recharts latency sparkline, circuit breaker state, SSE event counts, token usage charts
- [F-096] Enhanced Error Boundary — Branded error.tsx with copy diagnostics, SSE reconnect state, focus management
- [F-097] Full i18n Coverage — All components localized across 3 locales (en, pt-BR, es) including exports, accessibility, observability
- [F-098] Playwright E2E Golden Paths — 3 specs (onboarding wizard, language switch, SSE streaming) + axe-core a11y audit
- [F-099] Judge Artifacts — Architecture diagram (8 Mermaid), feature map (6 areas), demo script (3-min "Meet Ana"), judge packet (1-page)

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

## Backlog
- [F-035] Sign Language Post-MVP Path — SPOTER transformer + VLibrasBD NMT dataset (ADR-047)
