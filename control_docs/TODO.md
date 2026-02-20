# Sprint TODO

Status key: `[x]` done | `[~]` in-progress | `[ ]` planned

---

## Completed Sprints (S0-25)

All 26 sprints COMPLETED. 224 features (F-001 through F-224). ~3,600+ tests (2,348 runtime + 277 agents + 1,236 frontend). 0 lint/type errors. Docker 4 services healthy. See FEATURES.md for per-sprint detail.

---

## Sprint 26 — "Make the Invisible Visible" — DONE

### Backend Wiring (F-175/F-176/F-165/F-177)
- [x] Skills API wired to app factory with SessionFactorySkillRepository (F-176)
- [x] TTS router wired with ElevenLabs/FakeTTS fallback (F-165)
- [x] Skills workflow nodes integrated in plan + tutor workflows (F-177)
- [x] Settings: elevenlabs_api_key field, diagnostics endpoint updated

### Frontend — High-Impact Visual Features
- [x] Agent Pipeline Visualization — 6-node real-time graph with "Opus 4.6 Core" badge (F-217)
- [x] Adaptation Diff View — split-pane standard vs adapted with profile switching (F-218)
- [x] Evidence Panel — 6-section trust accordion (model, quality, standards, RAG, a11y, time) (F-219)
- [x] TTS Audio Player — play/pause, speed, language, voice selector (F-220)
- [x] Braille Download + Copy — download .brf, copy to clipboard (F-221)
- [x] Inclusive Classroom Mode — 4-student cockpit grid with accent colors (F-222)

### Quality
- [x] 15 ruff lint errors fixed
- [x] 2 TypeScript errors fixed (FeatureItem icon type, ReactNode cast)
- [x] ai_receipt SSE event type mismatch fixed
- [x] evidence-panel null-safety fixes
- [x] Docker frontend memory increased to 2G

---

## Sprint 27 — "Production-Grade Polish" (In Progress)

Based on GPT-5.2 backend architecture review + frontend UX review.

### Critical Fixes (done — from Mega Review v3)
- [x] F-243: Demo profile key mismatch — VALID_DEMO_PROFILES includes both short (login) and long (landing) keys
- [x] F-244: EvidencePanel aria-labelledby — missing id on toggle button
- [x] F-245: PreferencesPanel focus restore — stale closure fix
- [x] F-246: JWT iss/aud claims — mint when env vars configured
- [x] F-247: /auth/demo-login endpoint — proper JWT flow with short/long key aliases, 7 tests
- [x] F-248: Demo users seeded with hashed password (demo123), email login works
- [x] F-249: Login rate limit raised to 20/min for demo-friendly Docker testing
- [x] F-250: Docker frontend memory 512M → 2G, NODE_OPTIONS=--max-old-space-size=1536

### Phase 1 — Backend Hardening (HIGH IMPACT)
- [x] F-230: PostgresUserRepository — SessionFactoryUserRepository + DI wiring (d505bdd)
- [x] F-231: JWT Hardening — RS256/HS256 algorithm selection, jti claim + Redis blacklist, POST /auth/logout, configurable TTL
- [x] F-232: Health Diagnostics Split — public /health/diagnostics, private /internal/diagnostics

### Phase 2 — Frontend Premium Polish (HIGH VISUAL IMPACT)
- [x] F-233: Before/After Accessibility Compare Slider (d30daed)
- [x] F-234: Pipeline Edge Animations — SVG stroke-dashoffset + node glow states
- [x] F-235: Motor Accessibility Mode — MotorStickyToolbar, 56px targets, pill shapes, 12 tests
- [x] F-236: Micro-interactions — btn-press scale(0.97), slide-in animation, dash-flow keyframe

### Phase 3 — API & Observability
- [x] F-237: Run Resource Model — GET /runs (list+filter+pagination), GET /runs/{id} (detail)
- [x] F-238: RFC 7807 Error Model — already implemented (error_handler.py, 8 tests, application/problem+json)
- [x] F-239: TenantContext Explicit Dependencies — all routers use Depends(require_authenticated)

### Phase 4 — Cleanup & Polish
- [x] F-240: Config Deduplication — AiLineConfig deprecated with DeprecationWarning, Settings is canonical
- [x] F-241: Cache Skill Registry — _get_skills_info() cached once, used by diagnostics + capabilities
- [x] F-242: Demo Storyboard — 2 tracks (Teacher/Accessibility), 5 steps each, full i18n (4e0de99)

---

## Post-Hackathon (unscheduled)
- [ ] Postgres RLS, Redis rate limiter, disable OpenAPI in prod, SW multi-locale caching
- [ ] Teacher Skill Sets — per-teacher presets (F-178)
- [ ] Real assistive technology testing (axe-core E2E with NVDA/VoiceOver)
- [ ] Braille Grade 2 via liblouis
- [ ] SSE resumable runs — Redis Stream (XADD) keyed by run_id, Last-Event-ID replay
- [ ] Redis maxmemory eviction safety — separate DB indexes for ephemeral vs critical keys
- [ ] Rate limiting Redis persistence for restart survival
- [ ] Multi-tenant repo enforcement mixin (require tenant filtering on every query)
