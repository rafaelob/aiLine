---
name: claude-api
description: "Use when calling the Claude (Anthropic) Messages API or SDK in Python or TypeScript: model selection, streaming, tool use, structured JSON, thinking, prompt caching, vision, batches, API errors."
license: Apache-2.0
compatibility: Python 3.10+ (anthropic SDK) or Node 22+ (@anthropic-ai/sdk). Requires ANTHROPIC_API_KEY.
metadata:
  version: "2.6.5"
---

## Routing

Choose the smallest workflow that matches the request. Load a reference only when its topic is needed; otherwise use this root guide. Treat the workflow as a heuristic while preserving safety, protocol, schema, destructive-action, and artifact invariants. Provider/API facts remain where intrinsic to the named integration; executor or model choice does not change the contract.

# Claude API Reference

## Scope
- User is building an application that calls the Claude Messages API
- User needs help with Anthropic SDK setup (Python or TypeScript)
- User wants to implement tool use, streaming, or structured JSON output
- User is troubleshooting Claude API errors or unexpected behavior
- User wants to use thinking/extended reasoning

## Prerequisites
- Anthropic API key set as `ANTHROPIC_API_KEY` environment variable
- SDK installed: `pip install anthropic` (Python) or `npm install @anthropic-ai/sdk` (TypeScript)

## Quick Decision — Choose Your Surface

| Need | Use |
|------|-----|
| Single call (classify, summarize, generate) | Messages API |
| Multi-step pipeline with tools | Messages API + tool use loop |
| Structured JSON extraction | Messages API + `output_config.format` (primary) or tool use (alternative) |
| High-volume offline processing | Batches API |

## Workflow

### 1. Set up SDK

**Python:**
See references/EXAMPLES.md, Example 1, for this implementation path.

**TypeScript:**
See references/EXAMPLES.md, Example 2, for this implementation path.

### 2. Model selection defaults
- Highest capability: `claude-fable-5-1` — Anthropic's most capable widely released model (released 2026-09-01; active/latest; 1M ctx, 128k output, adaptive thinking always-on, default `high` effort; $10/$50 per MTok). It supports all five effort levels (`low`, `medium`, `high`, `xhigh`, `max`) and may require account/region enablement. `claude-mythos-5-1` is limited to approved Project Glasswing customers.
- Previous Fable generation: `claude-fable-5` — still supported for existing integrations (GA 2026-06-09; 1M ctx, 128k output, adaptive thinking always-on; $10/$50 per MTok). `claude-mythos-5` remains invitation-only (Project Glasswing).
- Flagship (Opus tier): `claude-opus-5` — Anthropic's current Opus-tier flagship (GA 2026-07-24; the bare model ID is both the snapshot and the alias — no dated snapshot exists). 1M ctx **GA by default and by maximum**, no beta header, no long-context premium; 128k output (Batch API up to 300k with header `output-300k-2026-03-24`); $5/$25 per MTok — identical to Opus 4.8; knowledge cutoff May 2026 (most recent of the family). **Adaptive-only**: `thinking:{"type":"enabled",...}` returns 400 (use `adaptive`); `{"type":"disabled"}` only works at `effort` <= `high` — `xhigh`/`max` combined with disabled thinking also returns 400. Citations, Files API, PDF support, and the memory tool are **not yet confirmed** for Opus 5 — do not assume parity with Opus 4.8 on those surfaces.
- Still supported (Opus tier): `claude-opus-4-8` — most capable Opus-tier before Opus 5, still excellent for complex reasoning and agentic coding; **not deprecated**, retirement not before 2027-05-28 (source: https://platform.claude.com/docs/en/about-claude/model-deprecations — `Model status` row reads `claude-opus-4-8 | Active | N/A | Not sooner than May 28, 2027`; verified_at 2026-09-17; recheck that table before relying on the date). Note the two official pages disagree in framing: models/overview now lists Opus 4.8 under **Legacy models (still available)** rather than in the current line-up, while model-deprecations still gives its state as `Active` — treat it as supported-but-no-longer-current and prefer `claude-opus-5` for new work. Unlike Opus 5, `{"type":"disabled"}` works at any `effort` level on Opus 4.8.
- Default (Sonnet tier): `claude-sonnet-5-5` — released 2026-09-28; $2 input / $10 output per MTok, cache read $0.20 / cache write $2.50 (source: https://www.anthropic.com/claude-sonnet-5-5, read 2026-09-28); ~30% faster and up to 30% cheaper per task than Sonnet 5. Best at well-scoped implementation, bug fixing and iteration; the Opus tier stays stronger on open-ended, sustained-judgment work (same source). Vendor guidance on effort: `high` is the API default; for agentic coding and multistep tool use start at `medium` for well-specified tasks and move to `high` for harder or longer ones; for chat and other latency-sensitive work start at `medium` or `low`; reach for `xhigh`/`max` only where evals show a quality gain (source: https://platform.claude.com/docs/en/build-with-claude/effort, read 2026-09-28). Fleet's subagent effort policy lives in the Fleet provider facts and subagent cards. Left unset, `effort` defaults to `medium` in Claude Code and `high` on the Claude Platform (same source). Supersedes `claude-sonnet-5`; see `references/claude-api-model-capability-matrix.md` for the `between_tools` setting, benchmarks, and what is still UNVERIFIED.
- Previous Sonnet generation: `claude-sonnet-5` — GA 2026-06-30; 1M ctx, 128k output; adaptive thinking on by default; $2/$10 per MTok. Still supported.
- Legacy Sonnet: `claude-sonnet-4-6` — still supported, old tokenizer; prefer `claude-sonnet-5-5` in new code
- Fast/cheap: `claude-haiku-4-5` (alias) or dated `claude-haiku-4-5-20251001`
- **Aliases are stable**. Dated snapshot IDs (e.g. `claude-haiku-4-5-20251001`) also work and pin behavior; prefer aliases for latest-in-family, dated IDs for reproducibility (verify the exact dated snapshot at https://platform.claude.com/docs/en/about-claude/models/overview)
- Context: Fable 5.1, Fable 5, Opus 5, Opus 4.8, Sonnet 5, Sonnet 5.5, and Sonnet 4.6: 1M tokens at standard pricing (no beta header required, source: https://platform.claude.com/docs/en/models/overview, read 2026-09-28). Haiku 4.5: 200K tokens
- Max output (sync Messages API): Fable 5.1 = 128k, Fable 5 = 128k, Opus 5 = 128k, Opus 4.8 = 128k, Sonnet 5 = 128k, Sonnet 5.5 = 128k, Sonnet 4.6 = 128k, Haiku 4.5 = 64k (source: https://platform.claude.com/docs/en/models/overview, read 2026-09-28)
- Migrating `claude-sonnet-5` → `claude-sonnet-5-5`: pricing unchanged; `thinking:{"type":"disabled"}` now returns 400 — send `thinking:{"type":"between_tools"}` instead to turn off up-front thinking (accepted at `low`/`medium`/`high` effort only, with no beta header; it takes no `display`, `budget_tokens`, or `block_binding` field). At `xhigh`/`max`, `between_tools` itself returns 400 — thinking cannot be turned off at those levels, so use adaptive thinking instead (omit `thinking`, or send `{"type": "adaptive"}`). With `between_tools` set, effort cannot change mid-conversation. Forced `tool_choice` (`any` or `tool`) now returns 400 too, including on the token-counting endpoint — every earlier Sonnet model accepted it, Sonnet 5.5 is the first to reject it; switch to `auto` with `strict: true` tools. Source: https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide, read 2026-09-28. See the capability matrix reference
- Migrating `claude-sonnet-4-6` → `claude-sonnet-5` is **not drop-in**: manual `thinking:{"type":"enabled",...}` returns 400 (use `adaptive`, or `{"type":"disabled"}` to turn off); recalibrate `effort` (Sonnet 5 `medium` ≈ 4.6 `high`, Sonnet 5 `high` ≈ 4.6 `max`); re-baseline `max_tokens`/cost for the new tokenizer (~1.0–1.35× tokens)
- Migrating `claude-opus-4-8` → `claude-opus-5` is **not drop-in either**: `enabled` thinking already returned 400 on Opus 4.8, but Opus 5 adds a second break — `{"type":"disabled"}` now also returns 400 at `effort` `xhigh`/`max` (Opus 4.8 allows `disabled` at any effort). Re-check any code path that disables thinking at high effort levels before switching.
- As of September 2026 -- verify current models at https://platform.claude.com/docs/en/about-claude/models/overview

### 3. Basic message

See references/EXAMPLES.md, Example 3, for this implementation path.

With a system prompt:
See references/EXAMPLES.md, Example 4, for this implementation path.

### 4. Streaming

See references/EXAMPLES.md, Example 5, for this implementation path.

### 5. Tool use

Define tools with JSON Schema `input_schema`. Claude returns `tool_use` content blocks when it wants to call a tool.

See references/EXAMPLES.md, Example 6, for this implementation path.

### 6. Structured output

Primary path is native: `output_config={"format": {"type": "json_schema", "json_schema": {"name": ..., "schema": {...}}}}`. The parameter is `output_config.format`, **not** `response_format` (that is an OpenAI pattern). Select the `text` content block; it contains guaranteed-valid JSON matching the schema. Native structured outputs are supported on Fable 5.1.

Alternative, when you also need real tool execution: define a tool whose `input_schema` is your output schema and force it with `tool_choice={"type": "tool", "name": "..."}` — the `tool_use` block's `input` is your structured data. Do not use this forced-choice form on Fable 5.1: `any` and `tool` return HTTP 400 there; use `auto` plus a clear instruction and `strict: true` instead.

Read `references/claude-api-structured-output.md` when you need the full Python examples for either path, or when choosing between the native format and the forced-tool approach.

### 7. Thinking / extended reasoning

Three modes apply across the family: `thinking={"type": "adaptive"}` (model decides; on by default on Sonnet 5), `{"type": "enabled", "budget_tokens": N}` (`N` >= 1024 and `<` `max_tokens`), and `{"type": "disabled"}`. Fable 5.1 has adaptive thinking always on: omit `thinking`, use `output_config.effort` to control depth, and do not send `enabled` or `disabled` because either returns HTTP 400.

The one most people get wrong: `enabled` **returns 400 on Opus 5, Sonnet 5, Opus 4.8, and Opus 4.7** — those are adaptive-only, so use `adaptive` and turn thinking off with `{"type": "disabled"}`. On Opus 5 alone, `disabled` itself returns 400 unless `output_config.effort` is `low`/`medium`/`high`.

Read `references/claude-api-extended-thinking.md` when you need the per-model mode-support table, the `display` option, or the adaptive / explicit-budget code examples.

### 8. Vision (image input)

See references/EXAMPLES.md, Example 7, for this implementation path.

### 9. PDF input (document blocks)

Send PDFs as `document` content blocks (source types: `base64`, `url`, or `file` for Files API). Put document blocks **before** text for best results.

- **Limits:** 600 pages (100 for 200K-context models); 32 MB; no password/encryption
- **Token cost:** ~1500–3000 tokens per page (text extraction + page images)
- For PDFs reused across requests, use the Files API (section 10) to avoid re-sending large payloads

See `references/claude-api-files-and-documents.md` for full base64 / URL / file_id code examples.

### 10. Files API (beta)

Upload files once (`client.beta.files.upload()`) and reference by `file_id` in `document` blocks across multiple requests. Requires beta header `files-api-2025-04-14`.

- **Accepted types:** PDF, JPEG/PNG/GIF/WebP, CSV, XLSX, DOCX, MD, TXT
- **Size limit:** 500 MB per file
- **SDK operations:** `upload()`, `list()`, `retrieve_metadata()`, `download()`, `delete()` — all under `client.beta.files`
- Combine with `cache_control` on the document block for maximum cost savings on reused documents

See `references/claude-api-files-and-documents.md` for upload, file_id usage, caching combination, and management operation examples.

### 11. Agent Skills in the code execution container (beta)

Mount a skill into a request by declaring the `code_execution` tool and listing it under `container`, with header `anthropic-beta: skills-2025-10-02`:

See references/EXAMPLES.md, Example 8, for this implementation path.

- **`type`** is `anthropic` (`pptx`, `xlsx`, `docx`, `pdf`) or `custom` (`skill_01...`, uploaded via `POST /v1/skills`); **max 8 per request**
- The container **persists**: the response returns `container: {id, expires_at}`; reuse it by passing the id as a plain string. It lives **30 days**, checkpointed after ~5 min idle — `expires_at` is a shorter rolling value, not that limit
- `stop_reason: "pause_turn"` is **not an error**: append the assistant response back unchanged and re-send to continue
- **This is not how Claude Code loads skills.** That path is filesystem discovery with no upload, no `container`, and full network access; this container has none

See `references/claude-api-agent-skills-in-container.md` for the CRUD/versioning endpoints, `container_upload` file flow, the Managed Agents comparison, and the two limits Anthropic does not publish.

### 12. Prompt caching (`cache_control`)

Mark stable content (system prompt, big context, tool schemas) so Anthropic caches the prefix; subsequent requests pay a reduced cache-read rate.

See references/EXAMPLES.md, Example 9, for this implementation path.

- `cache_control` is allowed on: text blocks, image blocks, document blocks, tool definitions, search result blocks, and tool result blocks
- Order matters: put stable content FIRST (system → tools → stable docs → dynamic user turn). Cache is prefix-based
- Up to 4 `cache_control` breakpoints per request
- Top-level `cache_control` (request-level) auto-applies to the last cacheable block

### 13. Batches API

For high-volume offline processing (50% cost discount, 24h SLA):

See references/EXAMPLES.md, Example 10, for this implementation path.

Opus 5, Opus 4.8, Opus 4.7, Opus 4.6, and Sonnet 4.6 support up to 300k output tokens on Batches with the `output-300k-2026-03-24` beta header.

### 14. Error handling
- **429** = rate limited — implement exponential backoff
- **529** = API overloaded — retry with backoff
- **400** = bad request — check model ID, params, message format
- Always wrap API calls in try/except and handle retries

## Gotchas
- **Prefilling returns 400 on Opus 4.8 and Sonnet 4.6** — Ending `messages` with an `assistant`-role turn is NOT supported on `claude-opus-4-8` or `claude-sonnet-4-6`; returns HTTP 400. It still works on Haiku 4.5 and older models. Use `output_config.format` (structured outputs) or system prompt instructions to constrain format on newer models (Sonnet 5 behavior on prefill is UNVERIFIED — confirm against models/overview before relying on it)
- **temperature/top_p/top_k are deprecated on Fable 5.1, Fable 5, Opus 5, Opus 4.7, Opus 4.8, and Sonnet 5** — sending a non-default value returns HTTP 400. Valid on Sonnet 4.6 and older models
- **Per-model capability matrix lives in a reference now** — the calls that return HTTP 400 are still listed here: `thinking:{"type":"enabled"}` on Sonnet 5, Opus 5, Opus 4.8 and Opus 4.7 (use adaptive); `thinking:{"type":"disabled"}` on Opus 5 above `effort: high`; `speed:"fast"` on `claude-opus-4-7`, which was removed and now errors instead of silently falling back; the `mid-conversation-tool-changes-2026-07-01` beta on Sonnet 5. Read `references/claude-api-model-capability-matrix.md` when you need the per-model table itself — which `effort` levels each model accepts, thinking-mode support, fast-mode pricing, tokenizer ratios, or which beta header is valid where.
- **thinking.display defaults to "omitted" on Fable 5.1, Fable 5, Opus 5, Opus 4.8, and Sonnet 5** — set `display: "summarized"` explicitly to receive thinking summaries. Fable 5.1 also supports `display: "updates"` behind the `thinking-display-updates-2026-08-18` beta header. On Fable 5.1 and Fable 5, thinking is always-on; setting `type: "disabled"` or manual `enabled` returns 400
- **Forced tool choice returns 400 on Fable 5.1** — `tool_choice: {"type": "any"}` and `{"type": "tool", "name": "..."}` are unsupported. Leave `tool_choice` at `auto` (or `none`) and use a clear instruction with `strict: true` when the model should call a schema-constrained tool
- **tool_result blocks must be FIRST in user content array** — placing any text content before `tool_result` blocks returns HTTP 400. Always put tool results before any accompanying text in the same user turn
- **Structured output has a native path** — Use `output_config.format` (not `response_format`, which is an OpenAI pattern). The tool-use approach still works and is useful when you also need tool execution
- **`system` is a top-level parameter** — it goes in `messages.create(system=...)`, NOT inside the messages array. `system` also accepts a list of content blocks when you need `cache_control`
- **Message role alternation** — messages must alternate user/assistant; consecutive same-role messages cause errors
- **Tool results are user messages** — send as `role: "user"` with `type: "tool_result"` content blocks referencing the `tool_use_id`
- **Always parse tool input properly** — use `json.loads()` / `JSON.parse()`, never regex
- **Image limits** — supported types: JPEG, PNG, GIF, WebP. Per-request image count cap is version-specific (UNVERIFIED as of 2026-04-21 against latest Vision docs); verify current limits at https://platform.claude.com/docs/en/build-with-claude/vision
- **Do not hardcode model IDs in variables** — keep them visible and greppable as string literals
- **Content is a list** — `message.content` is always a list of blocks, not a single string; select the block whose `type` is `text` because thinking blocks may precede it
- **Prompt caching order matters** — put stable content (system, tool schemas, big docs) before dynamic user input; cache is prefix-based

## Validation
- API calls return 200 with valid `Message` response object
- `message.content` contains expected block types (`text`, `tool_use`, `thinking`)
- Tool use calls have proper `input_schema` conforming to JSON Schema
- Streaming produces incremental text events
- Error handling covers 429, 529, and 400 status codes

## Companion skills
- `prompt-caching` — multi-provider prompt caching with breakpoints, TTL, pricing, ZDR eligibility (verified 2026-04-29).

## Versioning & freshness
- Models: `claude-fable-5-1` (highest capability, released 2026-09-01), `claude-fable-5` (prior Fable generation, GA 2026-06-09), `claude-opus-5` (Opus-tier flagship, GA 2026-07-24), `claude-opus-4-8` (still supported, not deprecated, retirement not before 2027-05-28), `claude-opus-4-7` (now Legacy), `claude-sonnet-5-5` (recommended Sonnet, released 2026-09-28, source https://www.anthropic.com/claude-sonnet-5-5 read 2026-09-28), `claude-sonnet-5` (previous Sonnet generation, GA 2026-06-30, still supported), `claude-sonnet-4-6` (legacy), `claude-haiku-4-5` (alias) / `claude-haiku-4-5-20251001` (dated). Legacy Sonnet 4 / Opus 4 (2025-05-14 snapshots) are deprecated, retired 2026-06-15 — do not use those IDs. Verify at https://platform.claude.com/docs/en/about-claude/models/overview.
- SDK: `anthropic` (Python), `@anthropic-ai/sdk` (TypeScript) -- verify at https://platform.claude.com/.
- Aliases track the latest in-family model; dated snapshot IDs pin behavior and are useful for reproducibility.
- **Context editing** (`platform.claude.com/docs/en/build-with-claude/context-editing`) and **compaction** are first-class long-context tools; the memory tool is available for durable agent state — reach for these before hand-rolling truncation.
- **Model IDs, pricing, context/output limits, thinking-mode contracts, `effort` levels, and beta headers in this skill are PERISHABLE** — re-verify at https://platform.claude.com/docs/en/about-claude/models/overview before any load-bearing use.

## Output format
When generating API integration code:
1. Complete, runnable code snippet with imports
2. Error handling included
3. Environment variable for API key (never hardcoded)
4. Comments explaining non-obvious parameters
