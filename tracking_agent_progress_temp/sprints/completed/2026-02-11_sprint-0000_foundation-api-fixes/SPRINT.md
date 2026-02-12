# Sprint 0000 — Foundation & API Fixes
**Status:** completed | **Date:** 2026-02-11

**Goal:** Fix all known API mismatches so the backend pipeline runs end-to-end,
create all control_docs, and pin dependencies.

---

## Scope / Stories

### S0-001: Fix DeepAgents API mismatches in planner [x]
- Changed `instructions=` to `system_prompt=` in `create_deep_agent()`
- Changed `agent.ainvoke(full_prompt)` to `agent.ainvoke({"messages": [...]})`
- Verified `response_format=` and `skills=` parameters

### S0-002: Fix Claude Agent SDK API mismatches in executor [x]
- Changed `PermissionMode.bypassPermissions` to string literal `"bypassPermissions"`
- Moved `mcp_servers` from constructor into `ClaudeAgentOptions`
- Replaced `client.query()` with `receive_response()` pattern
- Changed `client.close()` to `client.disconnect()`

### S0-003: Fix Tutor Agent session SDK mismatches [x]
- Applied same SDK fixes as S0-002 to tutoring/session.py

### S0-004: Add CORS middleware to FastAPI [x]
- Added CORSMiddleware with allow_origins=["*"] (dev)

### S0-005: Pin dependency versions in pyproject.toml [x]
- Pinned all major dependencies with exact versions

### S0-006: Create all control_docs/ files [x]
- Created 7 canonical files following template

### S0-007: Test pipeline end-to-end [x]
- Verified planner → validator → executor flow completes

## Decisions
- Fix in-place rather than rewrite to minimize risk
- Keep existing file structure; clean architecture refactor is Sprint 1

## Known Risks (from deep research — Feb 11)

**DeepAgents `structured_response` intermittency (GitHub issue #330):**
When tools are involved, `result.get("structured_response")` may intermittently
return None even with `response_format` set. Mitigation: implement fallback parser
that extracts structured data from `result["messages"][-1].content` when the key
is missing.

**Claude Agent SDK `receive_response()` must not be exited with `break`:**
Use flags instead. Let the async iterator complete naturally or the connection
may not clean up properly.

**DeepAgents default model is Claude Sonnet 4.5:**
Always pass explicit `model` parameter from SmartRouterAdapter config — do not
rely on the default.
