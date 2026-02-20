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

## Sprint 27 — "Production-Grade Polish" (Planned)

Based on GPT-5.2 backend architecture review + frontend UX review.

### Phase 1 — Backend Hardening (HIGH IMPACT)
- [ ] F-230: PostgresUserRepository — persistent auth across restarts (replace InMemoryUserRepository, wire via Container DI)
- [ ] F-231: JWT Hardening — RS256 issuance matching middleware config, jti claim + Redis blacklist for logout/revoke, shorter access TTL (15-60 min)
- [ ] F-232: Health Diagnostics Split — public /health/diagnostics (version, uptime, deps ok/degraded), private /health/diagnostics/internal (full payload, auth required)

### Phase 2 — Frontend Premium Polish (HIGH VISUAL IMPACT)
- [ ] F-233: Before/After Accessibility Compare Slider — draggable split-pane comparing standard vs persona themes with same content
- [ ] F-234: Pipeline Edge Animations — SVG stroke-dashoffset during running nodes, node glow states (idle/running/succeeded/failed/skipped)
- [ ] F-235: Motor Accessibility Mode — increased hit targets (pill-shaped clickable areas), sticky toolbar with big primary actions, visual tap zones
- [ ] F-236: Micro-interactions — button press scale(0.98) + shadow shift, SSE event slide-in animation, theme-aware skeleton shimmer (disabled in high_contrast/screen_reader)

### Phase 3 — API & Observability
- [ ] F-237: Run Resource Model — POST /plans:run → {run_id}, GET /runs/{id} (status + artifacts), GET /runs/{id}/events (SSE replay). Unifies plan/tutor patterns
- [ ] F-238: RFC 7807 Error Model — consistent {type, title, detail, instance, request_id} on all errors, OpenAPI reusable error components
- [ ] F-239: TenantContext Explicit Dependencies — Depends(get_actor) returning ActorContext {user_id, role, org_id}, repos accept ActorContext explicitly

### Phase 4 — Cleanup & Polish
- [ ] F-240: Config Deduplication — deprecate AiLineConfig dataclass in favor of Settings pydantic model
- [ ] F-241: Cache Skill Registry in Diagnostics — compute at startup or cache N seconds instead of scanning on every /health/diagnostics call
- [ ] F-242: Demo Storyboard — guided "Teacher story" + "Accessibility showcase" demo panels for 5-minute hackathon presentation

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
