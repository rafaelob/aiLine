# Security

## Compliance
- **LGPD** (Brazil) — user consent for data processing; right to deletion
- **FERPA** (US) — student education records protected; no PII in analytics
- No PII stored in accessibility profiles (disability type only, no medical data)

## Threat Model

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Prompt injection via student input | High | Input sanitization + system prompt injection guard + structured output enforcement |
| API key leakage | Critical | Secrets in env / GCP Secret Manager; never in repo; .gitignore enforced |
| Unauthorized data access | High | App-level tenant isolation (teacher_id from auth context only, never from request body) |
| Cross-tenant data leakage | High | Repository methods require teacher_id; cross-tenant integration tests |
| XSS in plan HTML output | Medium | DOMPurify sanitization (exports + Mermaid SVG); CSP headers |
| Denial of service | Medium | Rate limiting (FastAPI middleware); per-tenant cost guards |
| Insecure file upload | Medium | File type validation; size limits (10MB audio, 5MB image, 50MB doc) |
| LLM hallucination in tutor | Medium | RAG citations required; confidence threshold; "I'm not sure" fallback |
| Sign language misrecognition | Low | Confidence scores; human review flags; limited gesture vocabulary for MVP |

## Multi-Tenancy Security
- **Current:** Application-level tenant enforcement with composite FK constraints (ADR-012, ADR-053)
- **Planned:** Postgres RLS policies post-hackathon (defense-in-depth alongside app-level)
- Tenant identity derived from JWT/session auth context only
- TenantContext dependency injected into all API routes
- Repository signatures require teacher_id parameter
- Composite FK for parent-child: `lesson(teacher_id, course_id)` references `course(teacher_id, id)`
- No endpoint accepts raw teacher_id for authorization purposes
- Cross-tenant isolation tested: CRUD isolation, FK association leaks, pgvector search leaks

## Secrets Management
- Local: .env file (git-ignored via .gitignore)
- CI: GitHub Actions secrets
- Production: GCP Secret Manager
- Rotation: API keys rotated quarterly minimum
- Never commit: .env, credentials.json, *.key, *.pem
- Redis AUTH enabled (password via REDIS_PASSWORD env var)

## Access Control
- JWT RS256/ES256 verification with JWKS support, algorithm pinning, iss/aud/exp/nbf validation (F-100)
- 57 JWT security tests: forged, expired, wrong aud/kid, replay, tenant impersonation (F-101)
- Centralized authorization policy (authz.py): `require_authenticated`, `require_tenant_access`, `can_observe` (ADR-060)
- **All API endpoints require authentication** (media, sign-language, plans, tutors, materials, observability, traces, RAG diagnostics)
- WebSocket `/ws/libras-caption` requires JWT token via `?token=` query parameter
- CORS `X-Teacher-ID` header only allowed in dev mode (removed from production CORS)
- Roles: admin, educator, student
- Principle of least privilege on all service accounts

## Prompt Injection Defenses (F-102)
- **System prompt injection guard** prepended to all agent prompts (Planner, Executor, QualityGate, Tutor)
- Guard prohibits: revealing system prompts, cross-tenant access, code generation, ignoring instructions
- Document trust scoring for RAG retrieval
- Retrieval sanitization (instruction hierarchy)
- Structured output enforcement via Pydantic AI
- Structured audit logging for admin/content/auth events (F-103)

## XSS Prevention
- DOMPurify sanitization on: export HTML viewer, bionic text, Mermaid SVG output
- Mermaid SVG sanitized with SVG profile (forbids script, foreignObject, event handlers)
- CSP: `default-src 'self'`; `script-src 'self' https://vlibras.gov.br`
- X-Frame-Options: DENY; X-Content-Type-Options: nosniff

## Dependency Scanning
```bash
uv run pip-audit
pnpm audit
trivy image ailine-api:$(git rev-parse --short HEAD)
```

## Input Validation
- All API inputs validated via Pydantic models
- File uploads: size limits enforced per type; content-type checked
- Text inputs: null byte removal, NFC normalization, max length enforced
- LLM outputs: JSON schema validation for structured responses
- Metadata: depth-limited sanitization (max 3 levels, 100 items per list)
