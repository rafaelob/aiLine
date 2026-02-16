# Changelog
All notable changes documented here. Format: [Keep a Changelog](https://keepachangelog.com/).

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

### Added
- Public landing page — hero with mesh gradient, animated stat counters, feature cards, floating glass nav, "Built with Claude Opus 4.6" footer (F-146)
- Route group `(app)/` — authenticated pages with sidebar/topbar isolated from public landing (F-147)
- 86 new tests — landing page components, shared animated counter, extracted dashboard modules (F-153)
- Shared AnimatedCounter component with configurable spring physics (F-150)

### Improved
- Dashboard refactored: 541→362 LOC — extracted icons, plan history card, animated counter (F-149)
- All 327 ESLint warnings eliminated via config update + targeted fixes (F-148)
- Landing page WCAG AAA compliance — focus rings, aria-live counters, proper headings, reduced-motion (F-151)
- Landing UX premium polish — gradient text, scroll animations, hover depth effects (F-152)
- Security review — 0 critical/high findings across all uncommitted changes (F-154)
- Repository cleanup — .gitignore improvements, screenshot artifacts removed (F-155)
- Total: 1,875 backend + 250 agents + 1,048 frontend = **3,173 tests passing**

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
Scorecard (F-121), HITL Review (F-122), Progress Dashboard (F-123), Conversation Review (F-125), 115 new tests, 8 nav items. **2,900 tests.**

## [0.1.1] - 2026-02-14 (Excellence Sweep)
114 mypy → 0, LangGraph state leak fix, server-side translations, a11y landmarks, Ruff 0.

## [0.1.0] - 2026-02-13 — Hackathon Release (120 features, 60 ADRs, 2700+ tests)
