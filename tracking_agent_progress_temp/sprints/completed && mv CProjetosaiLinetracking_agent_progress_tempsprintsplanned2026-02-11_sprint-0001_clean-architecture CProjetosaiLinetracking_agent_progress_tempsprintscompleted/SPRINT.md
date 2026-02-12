# Sprint 0000 — Foundation & API Fixes

**Status:** completed | **Date:** 2026-02-11
**Goal:** Fix all known API mismatches so the backend pipeline runs end-to-end.

---

## Scope & Acceptance Criteria

All API call-sites in the runtime must match the actual SDK/library signatures
(DeepAgents 0.4.1, Claude Agent SDK 0.1.35, LangGraph 1.0.8). After this sprint
the planner, executor, and tutor can be invoked without import-time or call-time
exceptions, dependencies are pinned for reproducibility, and the project has its
canonical control_docs structure.

---

## Stories

### S0-001: Fix DeepAgents API mismatches [x]

**Description:** The planner was calling `create_deep_agent()` with the wrong
keyword argument and invoking the compiled LangGraph graph with a raw string
instead of the expected dict input format.

**Changes:**
- Changed `instructions=` to `system_prompt=` in `create_deep_agent()` call
  (verified against DeepAgents 0.4.1 API).
- Changed `agent.ainvoke(full_prompt)` to
  `agent.ainvoke({"messages": [{"role": "user", "content": full_prompt}]})`
  (LangGraph CompiledStateGraph requires a dict with a `messages` key).

**Files:** `runtime/ailine_runtime/planner_deepagents.py`

**Acceptance:** Planner callable without `AttributeError` or `TypeError`.

---

### S0-002: Fix Claude Agent SDK mismatches [x]

**Description:** The executor used outdated Claude Agent SDK patterns that no
longer matched the 0.1.35 release: enum-style permission mode, constructor-level
MCP server config, single-call query, and wrong teardown method.

**Changes:**
- `PermissionMode.bypassPermissions` (enum access) changed to
  `"bypassPermissions"` (string literal, which is what the SDK expects).
- `mcp_servers` parameter moved from the `ClaudeSDKClient` constructor into
  `ClaudeAgentOptions` (the SDK routes MCP config through the agent options
  object, not the client).
- Replaced single `client.query()` call with the two-step pattern:
  `client.query()` followed by `client.receive_response()`.
- `client.close()` changed to `client.disconnect()` (correct teardown method).

**Files:** `runtime/ailine_runtime/executor_agent_sdk.py`

**Acceptance:** Executor runs a full tool cycle without SDK exceptions.

---

### S0-003: Fix Tutor session SDK calls [x]

**Description:** The tutoring session module had the same Claude Agent SDK
mismatches as the executor since both were written against an earlier draft of
the SDK.

**Changes:**
- Applied identical fixes as S0-002 (string literal permission mode, MCP servers
  in agent options, two-step query/receive pattern, `disconnect()` teardown).

**Files:** `runtime/ailine_runtime/tutoring/session.py`

**Acceptance:** Tutor chat turn completes without SDK exceptions.

---

### S0-004: Add CORS middleware [x]

**Description:** The FastAPI app did not include CORS middleware, so browser-based
frontends could not make cross-origin requests (OPTIONS pre-flight failed).

**Changes:**
- Added `CORSMiddleware` to the FastAPI app with configurable origins.

**Files:** `runtime/ailine_runtime/api_app.py`

**Acceptance:** OPTIONS pre-flight responds 200 with correct CORS headers.

---

### S0-005: Pin dependency versions [x]

**Description:** Dependencies were unpinned, making builds non-deterministic and
risking silent breakage from upstream releases.

**Changes:**
- Pinned all core versions in `pyproject.toml`:
  - `deepagents==0.4.1`
  - `claude-agent-sdk==0.1.35`
  - `langgraph==1.0.8`
  - `langchain-anthropic==1.3.2`
  - `anthropic==0.79.0`
  - `fastapi==0.128.7`
  - `uvicorn==0.40.0`
- Added optional dependency groups: `[db]`, `[sqlite]`, `[mysql]`,
  `[embeddings-openai]`, `[embeddings-gemini]`, `[vectorstore-chroma]`,
  `[vectorstore-qdrant]`, `[media]`, `[redis]`, `[otel]`, `[all]`.
- Added dev dependencies: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`,
  `ruff`, `mypy`.

**Files:** `runtime/pyproject.toml`

**Acceptance:** `uv sync` succeeds and all versions are locked.

---

### S0-006: Create control_docs [x]

**Description:** The repository had no canonical documentation structure. Created
all seven required control_docs files.

**Changes:**
- Created: `TODO.md`, `FEATURES.md`, `SYSTEM_DESIGN.md`, `TEST.md`,
  `RUN_DEPLOY.md`, `CHANGELOG.md`, `SECURITY.md`.
- Total size: 346 lines (under the 500-line limit).

**Files:** `control_docs/TODO.md`, `control_docs/FEATURES.md`,
`control_docs/SYSTEM_DESIGN.md`, `control_docs/TEST.md`,
`control_docs/RUN_DEPLOY.md`, `control_docs/CHANGELOG.md`,
`control_docs/SECURITY.md`

**Acceptance:** All seven files exist and pass structure validation.

---

### S0-007: Expand .env.example and .gitignore [x]

**Description:** The `.env.example` was minimal and the `.gitignore` did not
cover common IDE, Node, Docker, and testing artifacts.

**Changes:**
- `.env.example`: added all config variables (LLM provider keys, embedding
  config, vectorstore config, database URL, Redis URL, media service keys,
  demo mode toggle).
- `.gitignore`: expanded with Node (`node_modules/`), IDE (`.idea/`, `.vscode/`),
  Docker (`docker-compose.override.yml`), and testing (`.coverage`, `htmlcov/`)
  patterns.

**Files:** `.env.example`, `.gitignore`

**Acceptance:** A new developer can copy `.env.example` to `.env` and start
without missing any required configuration variable.

---

## Dependencies

None (first sprint).

---

## Decisions

- **ADR-007:** DeepAgents for Planner, Claude Agent SDK for Executor. API
  signatures verified via research agent against published SDK sources.
- **ADR-009:** Pin all dependencies to exact versions for hackathon
  reproducibility. Loose version ranges deferred to post-MVP.

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| SDK APIs may change in minor releases | Exact version pins prevent drift |
| CORS wildcard in dev could leak to prod | Origin list driven by env var |
| DeepAgents is young library, sparse docs | Verified signatures from source |

---

## Completion Summary

All seven stories delivered. The runtime pipeline (planner, executor, tutor) is
callable without import or call-site exceptions. Dependencies are pinned,
control_docs structure is established, and the project is ready for the clean
architecture refactor in Sprint 1.
