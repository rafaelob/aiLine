# Changelog — frontend-ai-generative-ui

All notable changes to this skill are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]
### Changed
- Tightened activation routing around the skill's produced artifact and removed redundant handoff wording.

## [1.1.4] - 2026-08-07
### Fixed
- **Both `references/AI_UI_PATTERNS.md` citations were blind pointers** (`**Reference**:
  \`references/AI_UI_PATTERNS.md\`` with no reading trigger) per `AGENTS.md`'s rule that a
  citation without a "when/what's there" condition is never read. Checked the referenced file's
  actual headers against each citation site:
  - End of Step 2b (Vercel AI SDK Integration): the file's content matches — `useChat Pattern
    (React)`, `Server-Side Streaming (Route Handler)`, and `Legacy: streamUI (AI SDK RSC)` are
    exactly what Step 2b discusses. Gave it a trigger naming those three.
  - End of Step 2c (Multimodal Input Handling / File-Image Upload): the file has **no** content
    about multimodal input, file uploads, or provider payload limits — it is entirely chat UI /
    streaming / tool-call / generative-UI material. The citation there was a copy-paste of the
    2b citation with no matching content, not a legitimate second reference point. Removed it
    rather than invent a false trigger (writing a condition the file cannot honor is worse than
    a blind pointer — `AGENTS.md`).

## [1.1.3] - 2026-08-06
### Changed
- Moved the `## Freshness` section out of `SKILL.md`'s body (provenance-out-of-body pass, per
  `AGENTS.md` §"O que vai dentro de um SKILL.md"). Two facts it carried that weren't already
  in the body were promoted instead of archived: the per-provider streaming specifics (OpenAI
  Responses API preference, Anthropic's typed SSE event names, "use `google-genai`, never
  `google-generative-ai`" -- now in Step 2's Alternatives paragraph) and the "verify the
  installed SDK version before applying hook signatures" instruction (now right after it).
  Renamed the surviving link list to `## Sources`. Everything else duplicated body content
  already in Step 2b/Step 2c/Step 4, or was pure procedência, archived below:
  - Verified 2026-06-29 against ai-sdk.dev, OpenAI, Anthropic, and Google Gemini docs. Added
    (already in the body since that pass): multimodal file upload proxying and the Code
    Interpreter artifact download pipeline.
  - 2026-07-28: renamed "Common Pitfalls" to "Common Pitfalls / Gotchas" for the linter's
    checklist/gotcha heading pattern. No procedural content changed.

## [1.1.2] - 2026-07-30
### Changed
- Distribution level flipped user->project (owner decision recorded in
  reports/level_flip_decisions.json): always-on discovery cost was not
  justified by measured stack reach; now installed only where the stack
  evidence exists.

## [1.1.1] - 2026-07-28
### Changed
- Tightened description to <=400 chars (token-budget audit 2026-07-28); no negative routing existed in the original description, none added
