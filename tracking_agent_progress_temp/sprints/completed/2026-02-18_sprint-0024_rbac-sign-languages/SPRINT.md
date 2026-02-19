# Sprint 24 — RBAC System + International Sign Languages

**Status:** completed
**Start:** 2026-02-18
**End:** 2026-02-18
**Goal:** Implement role-based access control (5 roles) and international sign language support (8 languages)

## Scope

### Part A: RBAC System
- [x] A1: Database migration — `users` table with role enum, `organizations` table (F-206, F-207)
- [x] A2: Domain entities — UserRole enum, User model, Organization model, StudentProfile (F-205)
- [x] A3: Auth middleware — extract role/org_id from JWT claims, contextvars (F-208)
- [x] A4: authz.py — role-based authorization: require_role, require_admin, can_access_student_data (F-209)
- [x] A5: Auth API router — /auth/login, /auth/me, /auth/register, /auth/roles (F-210)
- [x] A6: Demo profiles — 2 admin profiles (school_admin, super_admin), total 8 (F-211)
- [x] A7: Frontend login page — role-based login with demo profiles + email/password (F-214)
- [x] A8: Frontend auth store — Zustand persist with JWT + user profile (F-213)
- [x] A9: Auth path exclusion fix — /auth/me works with auth (F-212)
- [x] A10: Frontend auth headers priority — JWT from store checked first (F-216)
- [x] A11: Tests — 184+ new tests (RBAC authz, auth endpoints, user entities)

### Part B: International Sign Languages
- [x] B1: Sign language registry — 8 languages with metadata, 8 gestures each (F-201)
- [x] B2: GlossToTextTranslator — 8 per-language LLM system prompts (F-202)
- [x] B3: Sign language discovery API — 4 new endpoints (F-203)
- [x] B4: WebSocket language selection via ?lang= query param (F-204)
- [x] B5: Frontend sign language selector — ARIA combobox with 8 languages (F-215)
- [x] B6: Tests — 76 sign language registry tests

## Acceptance Criteria
- [x] 5 roles: super_admin, school_admin, teacher, student, parent
- [x] JWT claims include `role` and `org_id`
- [x] Login page with role selection + demo profiles
- [x] 8 sign languages with per-language metadata and gestures
- [x] All existing tests still pass (2,155 runtime, 277 agents, 1,116 frontend)
- [x] 235 new tests for RBAC + sign languages
- [x] Docker Compose 4 services healthy
- [x] 0 lint/type errors (ruff, mypy, tsc, eslint)

## Verification
- Runtime (Docker): 2,155 passed, 3 skipped, 0 failures
- Agents: 277 passed, 0 failures
- Frontend: 1,116 passed (125 test files), 0 failures
- Total: **3,548 tests passing** (up from 3,313)
- Features: F-201 through F-216 (16 new features, total 216)
