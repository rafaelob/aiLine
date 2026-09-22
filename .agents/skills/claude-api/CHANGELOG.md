# Changelog — claude-api

All notable changes to this skill are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [2.6.4] - 2026-09-05
### Changed
Moved 10 implementation examples from the root into conditional references/EXAMPLES.md loading points while preserving their content.

## [2.6.3] - 2026-09-05
### Changed
- Added conditional root routing and removed redundant first-level pairing prompts from the activation description; detailed material remains available through workflow-selected references.

## [2.6.2] - 2026-09-04
### Changed
- Added Claude Fable 5.1 (`claude-fable-5-1`) to model selection, limits, effort, thinking,
  structured-output, and capability guidance. Fable 5.1 is active/latest with a 1M context,
  128K output limit, always-on adaptive thinking, default `high` effort, and $10/$50 per MTok.
- Documented Fable 5.1's HTTP 400 behavior for forced `tool_choice` values `any` and `tool`,
  the `thinking.display=updates` beta, and its rejection of manual `enabled`/`disabled`
  thinking configuration. Updated the Sonnet 5 price to its current standard $2/$10 rate.
  Sources checked 2026-09-04: https://platform.claude.com/docs/en/models/fable-5-1/overview,
  https://platform.claude.com/docs/en/claude_api_primer,
  https://platform.claude.com/docs/en/build-with-claude/effort, and
  https://platform.claude.com/docs/en/about-claude/pricing.

This file is the skill's ONLY dated history. Log every re-verification pass here.

## [2.6.1] - 2026-08-06
### Changed
- **Folded `references/claude-api-freshness-log.md` into this file and deleted it.** The previous
  pass moved the six dated re-verification entries out of the body into that file and recorded,
  in this changelog, that it had left "a second parallel history" for a later pass to resolve.
  One question — when was this fact last checked — answered in two places is the failure mode
  where whichever copy ages alone starts lying; the entries are now under
  "Re-verification history" below, verbatim and with their original dates. That file also opened
  by pointing at "the skill's inline `## Freshness`", a section the 2026-08-06 body cleanup had
  already removed, so it was citing something that no longer existed.
- Dropped the `references/claude-api-freshness-log.md` read trigger from
  `## Versioning & freshness`. The perishability instruction it sat next to — re-verify model
  IDs, pricing, limits, thinking contracts, `effort` levels and beta headers against the official
  model overview before load-bearing use — is unchanged, and is the part that alters behavior.

## [2.6.0] - 2026-08-06
### Changed
- Dismantled the `## Freshness` diary out of the body (token-budget/procedência audit, 2026-08-06). Live facts and instructions it was carrying — the broadened "these facts are perishable, re-verify before load-bearing use" instruction, `claude-opus-4-7` now Legacy, context editing/compaction/memory tool as long-context primitives, and the Legacy Sonnet 4 / Opus 4 retirement date — were promoted into `## Versioning & freshness`, which already held the skill's other live model/SDK facts. Everything else below is what was purely audit trail.
- 2026-07-28: split the six per-model capability matrices out to `references/claude-api-model-capability-matrix.md` to clear the 5k-token L2 cap. Every HTTP-400 trap they described stays summarized inline in `## Gotchas`; all UNVERIFIED caveats untouched.
- Last reviewed 2026-07-28 against the official model overview.
- Confirmed (2026-07-28 review): Opus 4.8 (flagship) / Sonnet 4.6 / Haiku 4.5 canonical IDs; 1M context on Opus 4.8 and Sonnet 4.6; 200k on Haiku 4.5; max output 128k/128k/64k — already stated verbatim in `### 2. Model selection defaults`, so nothing to promote beyond the Opus 4.7 Legacy status (moved to `## Versioning & freshness`).
- Confirmed (2026-07-28 review): `output_config.format` with JSON schema and `effort` level; `thinking` modes `adaptive` / `enabled` (with `budget_tokens`) / `disabled`; `cache_control` with `ttl` of `5m` (default) or `1h`; max 4 breakpoints per request; top-level `cache_control` auto-applies to last cacheable block — already stated verbatim in `### 6`, `### 7`, and `### 12`, so nothing to promote.
- Confirmed (2026-07-28 review): prefilling the assistant turn returns 400 on Opus 4.8 and Sonnet 4.6 — already stated verbatim in `## Gotchas`, so nothing to promote.
- Confirmed (2026-07-28 review): Opus 4.8 and Opus 4.7 support adaptive thinking only; Haiku 4.5/Opus 4.5/Sonnet 4.5 support enabled-only; Sonnet 4.6 and Opus 4.6 support both — this per-model table is already carried verbatim in `references/claude-api-model-capability-matrix.md` (split out the same day), so nothing to promote.
- UNVERIFIED-within-budget note on the exact per-request image count cap (2026-04-21) — already stated verbatim in `## Gotchas` under "Image limits", so nothing to promote.
- Structural, 2026-07-28: extracted sections 6 (structured output) and 7 (thinking / extended reasoning) verbatim into `references/claude-api-structured-output.md` and `references/claude-api-extended-thinking.md`, each replaced by an essentials + load-trigger stub — the body was ~6.5k tokens against the 5k L2 soft cap. No technical fact, model ID, parameter, or code sample changed.
- Structural, 2026-07-28: split the 6 dated re-verification entries (2026-06-04 -> 2026-07-28) out to `references/claude-api-freshness-log.md`; the live `Confirmed:` and `UNVERIFIED` caveats were kept inline verbatim at the time. No technical fact changed. (Reversed in 2.6.1 — see above.)

## Re-verification history

Dated passes that predate this changelog, moved here verbatim from the deleted
`references/claude-api-freshness-log.md`.

- **Re-verified 2026-07-28** against a live fetch of https://platform.claude.com/docs/en/about-claude/models/overview: confirmed Claude Opus 5 ($5/$25 per MTok, 1M ctx, 128k output, adaptive-only thinking, May 2026 knowledge cutoff) and Claude Sonnet 5 ($3/$15 standard, $2/$10 intro through 2026-08-31) exactly match this file's existing tables — no pricing/context/output-limit drift found. Confirmed Opus 4.8 still listed as current and supported (non-deprecated) on the official page. Added one new fact not previously captured: `effort` defaults to `high` when unset, on the Claude API and Claude Code for Opus 5 and Sonnet 5, and on all surfaces for Opus 4.8 (Gotchas, `output_config.effort` bullet). Noted for the record (not added to this skill, out of scope): the official page shows `claude-opus-4-1-20250805` as newly deprecated, retiring 2026-08-05 — this skill does not reference Opus 4.1. Left the Sonnet 5 prefill-behavior and sampling-params (temperature/top_p/top_k) UNVERIFIED hedges in Gotchas unchanged — the models-overview page does not resolve either question.
- **Re-verified 2026-07-27** against `guia_completo_agentes/guia_claude_api.html` (+ `guia_token_counting.html`): added Claude Opus 5 (`claude-opus-5`, GA 2026-07-24) as the Opus-tier flagship — bare ID is both snapshot and alias; 1M context GA by default AND maximum with no beta header and no long-context premium; 128k output (300k on Batches with `output-300k-2026-03-24`); $5/$25 per MTok, identical to Opus 4.8; minimum cacheable 512 tokens; knowledge cutoff May 2026. Documented the Opus 5 contract break consistently across the model-selection notes, the thinking-mode table, the adaptive-thinking note, and the Gotchas section: `thinking:{"type":"enabled"}` returns 400 (adaptive-only, same as Opus 4.8), and unlike Opus 4.8, `{"type":"disabled"}` itself returns 400 above `effort` `high` (`xhigh`/`max` blocked). Kept Opus 4.8 in all tables — confirmed NOT deprecated, retirement not before 2027-05-28. Added fast-mode pricing ($10/$50, 2x, research preview) and the Opus 4.7 fast-mode removal (now errors instead of silently falling back to standard). Added two new betas: `mid-conversation-tool-changes-2026-07-01` (not valid on Sonnet 5) and `fallbacks` mode `"default"` under header `server-side-fallback-2026-07-01`. Left the Sonnet 5 prefill-behavior hedge (Gotchas, prefill bullet) and the Sonnet 5 temperature/top_p/top_k hedge (Gotchas, sampling-params bullet) UNVERIFIED and unchanged — this refresh's source resolves the Opus 5 thinking contract but does not resolve either open question for Sonnet 5.
- **Re-verified 2026-07-05** against `guia_completo_agentes/guia_claude_api.html` + `guia_token_counting.html`: added Claude Sonnet 5 (`claude-sonnet-5`, GA 2026-06-30) as the recommended Sonnet default and demoted `claude-sonnet-4-6` to Legacy (still supported). Sonnet 5 uses adaptive thinking on by default (manual `enabled` → 400; disable via `disabled`), the new tokenizer (~1.0–1.35× tokens), all 5 effort levels (`max` is the ceiling, not `xhigh`), `thinking.display` defaults to `"omitted"`, intro pricing $2/$10 until 2026-08-31 then $3/$15. Documented the non-drop-in 4.6→5 migration (thinking 400, effort recalibration, tokenizer/cost re-baseline). Updated generic code examples to `claude-sonnet-5`; kept the extended-thinking `enabled` example on 4.6 (behavior-specific). Sonnet 5's prefill and sampling-param (temperature/top_p/top_k) 400 behavior left UNVERIFIED — not asserted.
- **Re-verified 2026-06-29**: corrected Sonnet 4.6 max output to 128k (was incorrectly listed as 64k); updated thinking-mode deprecation: `enabled`/`budget_tokens` is DEPRECATED on Opus 4.6 and Sonnet 4.6 per official adaptive-thinking docs; Opus 4.8 and Opus 4.7 return 400 on enabled mode; Haiku 4.5, Opus 4.5, and Sonnet 4.5 are enabled-only (no adaptive). Updated "as of" inline date to June 2026. Added 8 high gaps from guia_claude_api.html: temperature/top_p/top_k deprecated on Opus 4.7/4.8/Fable 5 (returns 400); prefilling returns 400 on Opus 4.8 and Sonnet 4.6 (was incorrectly marked "supported"); new tokenizer on Opus 4.7+/Fable 5 produces ~30% more tokens; output_config.effort parameter (low/medium/high/xhigh/max); thinking.display defaults to "omitted" on Opus 4.8; tool_result blocks must be FIRST in user content array; Files API (beta: files-api-2025-04-14); PDF document blocks.
- **Re-verified 2026-06-19**: added Claude Fable 5 (`claude-fable-5`, GA 2026-06-09, most capable widely-released model, $10/$50 per MTok) and Claude Mythos 5 (`claude-mythos-5`, invitation-only, Project Glasswing). Haiku latest remains 4.5 — no Haiku 4.6 exists.
- **Checked 2026-06-04** against https://platform.claude.com/docs/en/about-claude/models/overview (Opus 4.8 flagship; Opus 4.7 now Legacy) and https://platform.claude.com/docs/en/api/messages.
