# Agent Skills mounted in the code execution container — full reference

> Companion file to `claude-api/SKILL.md`. Load it when mounting an Agent Skill into a Messages API
> request, or when creating/versioning a custom skill through the API. It is NOT a standalone skill.

Every fact below was verified against `platform.claude.com` on **2026-07-28**. This surface is in
beta and is the kind of thing that moves: re-check the beta header and the endpoint shapes before
relying on them.

**This is not how Claude Code loads skills.** Claude Code and the Agent SDK read `SKILL.md` from the
filesystem (`.claude/skills/`, `~/.claude/skills/`) with no upload and no endpoint. What follows is a
different mechanism that happens to share the name — an uploaded bundle mounted into a sandboxed
container for one request. Confusing the two is the most likely error here.

---

## 1. Minimum working request

```json
{
  "model": "<current model>",
  "tools": [{"type": "code_execution_20260521", "name": "code_execution"}],
  "container": {"skills": [{"type": "anthropic", "skill_id": "pptx", "version": "latest"}]},
  "messages": [{"role": "user", "content": "Build a deck from this data"}]
}
```

Header: `anthropic-beta: skills-2025-10-02`.

Three things are load-bearing and each fails differently if omitted:

- **The beta header is still required.** Skills have not gone GA.
- **The `code_execution` tool must be declared.** A skill mounts *into* that tool's container; without
  the tool there is nowhere to mount it. The tool itself **is GA** — `code_execution_20250825`,
  `code_execution_20260120`, and `code_execution_20260521` (newest) all work without their own beta
  header. Older `code-execution-*` beta headers remain valid opt-ins but are now redundant, which is
  why some older doc examples still send them.
- **`container` is where skills live**, not `tools`.

## 2. `container.skills[]` entry shape

| Field | Required | Values |
|---|---|---|
| `type` | yes | `"anthropic"` (managed) or `"custom"` (yours, uploaded) |
| `skill_id` | yes | short name for anthropic (`pptx`, `xlsx`, `docx`, `pdf`); `skill_01...` for custom |
| `version` | no | defaults to `latest`; date-based for anthropic (e.g. `20251013`), Unix epoch for custom |

**Maximum 8 skills per request.** Four Anthropic-managed skills exist today: `pptx`, `xlsx`, `docx`,
`pdf`.

## 3. Container lifecycle — the part that surprises people

The container **persists across requests**. The response carries a top-level `container: {id, expires_at}`,
and a later request reuses it by passing the id as a plain string instead of an object:

```json
"container": "$CONTAINER_ID"
```

- The container expires **30 days after creation**.
- After roughly **5 minutes idle** it is checkpointed, then restored on next use inside the 30-day window.
- **`expires_at` is a shorter rolling value and does not represent the 30-day limit** — reading it as
  the container's lifetime is the trap here.
- An expired container cannot be reused; the request errors. Re-sending with no `container` creates a
  fresh one, which also means the reuse silently stops saving you anything if you never check.

## 4. Getting files in and out

- **In**: upload with `POST /v1/files` (`multipart/form-data`), beta header `files-api-2025-04-14`,
  then reference it in the message with `{"type": "container_upload", "file_id": "file_..."}`.
- **Out**: files the skill produces appear as `file_id` under
  `bash_code_execution_tool_result.content.content[]`. Download with
  `GET /v1/files/{file_id}/content`, same beta header.

The Files API carries its **own** beta header, separate from `skills-2025-10-02`. A request that
mounts a skill and uploads a file needs both.

## 5. `pause_turn`

A `stop_reason` of `pause_turn` means the server-side sampling loop hit its iteration limit (default
10 per request) while running server tools, or paused a long-running operation. **It is not an error
and not a refusal.**

To continue: append the assistant response back into `messages` **unchanged** and re-send. To stop
instead, modify the content before re-sending. Treating `pause_turn` as a failure and retrying from
scratch is the expensive mistake — it discards completed work and re-runs it.

## 6. Custom skills — the CRUD surface

| Operation | Endpoint |
|---|---|
| Create | `POST /v1/skills` |
| List | `GET /v1/skills` (filter by `source`) |
| Get | `GET /v1/skills/{skill_id}` |
| Delete | `DELETE /v1/skills/{skill_id}` |
| Create version | `POST /v1/skills/{skill_id}/versions` |
| List versions | `GET /v1/skills/{skill_id}/versions` |
| Get version | `GET /v1/skills/{skill_id}/versions/{version}` |
| Delete version | `DELETE /v1/skills/{skill_id}/versions/{version}` |
| Download content | `GET /v1/skills/{skill_id}/versions/{version}/content` (zip) |

Creation payload is **`multipart/form-data` with a `files` field** — a zip, or the individual files.
Not base64, not a JSON body. The returned `skill_id` looks like `skill_...`; the returned `version` is
a Unix epoch timestamp string (e.g. `"1759178010641129"`), which is why custom-skill versions do not
look like the date-based Anthropic ones.

## 7. Same word, three different mechanisms

| Surface | How a skill attaches | Header | Ceiling |
|---|---|---|---|
| Messages API | `container.skills[]` per request | `skills-2025-10-02` | 8 per request |
| Managed Agents | `skills: [...]` once at `POST /v1/agents` | `managed-agents-2026-04-01` | 500 per session |
| Claude Code / Agent SDK | filesystem discovery, no upload | none | n/a |

Two consequences worth carrying: Managed Agents attach skills **at agent creation, not per message**,
and more attached skills means the session sandbox takes longer to start. The Messages API container
has **no network access**; the Claude Code filesystem path has full network access — so a skill that
works in one can fail in the other for reasons that have nothing to do with the skill.

## 8. Limits — including what is not documented

- Skills per Messages API request: **8**.
- Skills per Managed Agents session: **500**, summed across all agents in the session.
- **Maximum skill/zip size: NOT DOCUMENTED.** Not stated on the overview, enterprise, guide, or API
  reference pages as of 2026-07-28. Measure before depending on a large bundle.
- **Execution timeout: NOT DOCUMENTED as a single number.** What is published: a **90-second** limit
  per REPL cell in programmatic tool calling, and a **5-minute minimum billing** per execution. The
  error `execution_time_exceeded` exists, but its threshold is not stated.

Do not fill either gap with a guess. An assumed size limit that is wrong fails at upload; an assumed
timeout that is wrong fails halfway through a user's job.

## Authoritative sources

- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview.md
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart.md
- https://platform.claude.com/docs/en/build-with-claude/skills-guide.md
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool.md
- https://platform.claude.com/docs/en/api/beta/skills.md
- https://platform.claude.com/docs/en/build-with-claude/files.md
- https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons.md
- https://platform.claude.com/docs/en/managed-agents/skills.md
