# Security

## Compliance
- **LGPD** (Brazil) — user consent for data processing; right to deletion
- **FERPA** (US) — student education records protected; no PII in analytics
- No PII stored in accessibility profiles (disability type only, no medical data)

## Threat Model

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Prompt injection via student input | High | Input sanitization + LLM guardrails + structured output enforcement |
| API key leakage | Critical | Secrets in env / GCP Secret Manager; never in repo; .gitignore enforced |
| Unauthorized data access | High | App-level tenant isolation (teacher_id from auth context only, never from request body) |
| Cross-tenant data leakage | High | Repository methods require teacher_id; cross-tenant integration tests |
| XSS in plan HTML output | Medium | DOMPurify sanitization; CSP headers; sandboxed iframe for exports |
| Denial of service | Medium | Rate limiting (FastAPI middleware); Redis-backed token bucket |
| Insecure file upload | Medium | File type validation (PDF/DOCX/TXT only); size limits (50MB); virus scan |
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

## Access Control
- JWT-based auth (pluggable via auth middleware)
- Roles: admin, educator, student
- Principle of least privilege on all service accounts
- Direct Anthropic API tool calling (Claude Agent SDK removed per ADR-048)

## Dependency Scanning
```bash
uv run pip-audit
pnpm audit
trivy image ailine-api:$(git rev-parse --short HEAD)
```

## Input Validation
- All API inputs validated via Pydantic models
- File uploads: MIME type + magic bytes validation
- Text inputs: max length enforced, HTML stripped
- LLM outputs: JSON schema validation for structured responses
