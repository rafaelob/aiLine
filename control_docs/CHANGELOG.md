# Changelog
All notable changes documented here. Format: [Keep a Changelog](https://keepachangelog.com/).

## [0.5.0] - 2026-02-15 (State-of-the-Art Final Sweep)

### Added
- Command Palette (Cmd+K / Ctrl+K) — fuzzy search, 9 page navigation, quick actions, theme + language switching, ARIA combobox (F-141)
- 21 new frontend tests (command palette, refactored components)

### Improved
- Refactored `_plan_nodes.py`: 764 LOC → 15 LOC barrel + 5 focused modules (F-142)
- Refactored `plan-generation-flow.tsx`: 757 LOC → 379 + 358 + 104 LOC (F-143)
- Extracted shared motion variants from 9 components into `lib/motion-variants.ts` (F-144)
- Fixed 3 unsafe `as never` casts with proper types in SSE hooks (F-145)
- Updated all docs to consistent numbers: 145 features, 3,087 tests, 20 sprints
- Total: 1,875 backend + 250 agents + 962 frontend = **3,087 tests passing**

## [0.4.0] - 2026-02-15 (Impact Sweep & State-of-the-Art Polish)

### Added
- View Transition Theme Morphing — circular clip-path reveal from click origin on persona switch (F-136)
- Loading skeletons for all 8 page routes — page-specific layout skeletons (F-137)
- Mobile Nav overflow menu — "More" popover for Materials, Sign Language, Observability, Settings (F-138)
- 51 new API tests — Progress (16), Plan Review (18), Tutor Transcript/Flag (17) (F-139)
- PreferencesPanel View Transition support (F-140)

### Improved
- All mobile pages now reachable (was missing 4 via mobile nav)
- `useViewTransition` hook supports typed transitions ('route' | 'theme') with origin coordinates
- Reduced-motion users see instant theme swap (no clip-path animation)
- Total: 1,875 backend + 250 agents + 941 frontend = **3,066 tests passing** (updated to 3,087 in Sprint 19)

## [0.3.0] - 2026-02-15 (Hackathon Final Push)

### Added
- Settings Page — AI model, language, accessibility, about sections with glass morphism (F-126)
- Guided Demo Mode — `?demo=true` auto-fills wizard, floating tooltip overlay, 3-step guided tour (F-127)
- Trust & Transparency Panel — quality report, scorecard, model provenance, decision badge in plan tabs (F-128)
- Materials Upload Page — file upload, material listing with tags, glass card grid (F-129)
- Live Dashboard Stats — wired to API endpoints, plan history cards, loading skeleton (F-130)
- Tutor Persistence — Zustand persist middleware, ConversationReview tab (F-131)
- System Status Indicator — TopBar health check badge with dropdown details (F-132)
- 44 new frontend tests (964 total, 113/114 files passing)

### Fixed
- 9 RUF009 lint errors (os.getenv in dataclass defaults → field default_factory) (F-133)
- 2 UP038 lint errors (isinstance tuple → union syntax)
- React Compiler cascading-render warning in plan-generation-flow.tsx
- Dead `/settings` sidebar link now has a corresponding page
- ESLint: 0 errors (was 1)
- Ruff: 0 errors (was 11)
- mypy: 0 errors across runtime (159 files) + agents (29 files) — was 44 errors

### Improved
- Wired 4 orphaned components: CognitiveLoadMeter→Accessibility, DegradationPanel→Observability, PersonaHUD→Accessibility, PrivacyPanel→Settings (F-134)
- Removed 5 duplicate/unused components and 5 test files (F-135)
- i18n: perfect 3-locale parity (en, pt-BR, es) verified across all 780+ keys
- All 9 sidebar nav links verified with corresponding pages
- Total: 1,821 backend + 250 agents + 931 frontend = **3,002 tests passing**

## [0.2.0] - 2026-02-14 (Hackathon Victory Sprint)

### Added
- Transformation Scorecard — 9-metric trust card computed as LangGraph terminal node (F-121)
- HITL Teacher Review Panel — approve/reject/revision workflow + pending reviews badge (F-122)
- Student Progress Dashboard — mastery tracking, standards heatmap, class overview (F-123)
- Conversation Review — scrollable tutor transcript with per-turn flagging (F-125)
- Reusable EmptyState and Skeleton loading components
- 3 new backend routers: progress (record/dashboard/student), review (approve/reject/pending), transcript (flag)
- 115 new tests (81 backend + 34 frontend) covering all Sprint 16 features
- i18n keys for all new features across 3 locales (en, pt-BR, es)
- 8 sidebar nav items (was 5): added sign-language, progress, observability

### Improved
- "Powered by Claude Opus 4.6" badge in sidebar footer (F-124)
- Sidebar and MobileNav expanded with progress, observability, sign-language routes
- Pipeline store: scorecard field extracted from SSE `run.completed` payload
- Total: 1,821 backend + 250 agents + 829 frontend = **2,900 tests passing**

## [0.1.1] - 2026-02-14 (Excellence Sweep)
114 mypy errors → 0, LangGraph state leak fixed, server-side getTranslations, a11y landmark fixes, Ruff 0 errors. Pydantic AI 1.58 model prefix compliance, Gemini 3 Flash default, README rewritten for judges.

## [0.1.0] - 2026-02-13 (Hackathon Release)
Hexagonal arch, 4 Pydantic AI agents, LangGraph workflows, SmartRouter, 3 LLM adapters, FastAPI+SSE, SQLAlchemy+pgvector, RAG pipeline, Next.js 16, 9 WCAG themes, 3 locales, JWT+JWKS, OTel, Docker Compose. 120 features, 60 ADRs, 2700+ tests.
