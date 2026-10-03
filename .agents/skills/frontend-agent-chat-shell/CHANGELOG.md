# Changelog: frontend-agent-chat-shell

All notable changes to this skill are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]
### Changed
- Tightened activation routing around the skill's produced artifact and removed redundant handoff wording.
- SKILL.md body hygiene (2026-08-06): moved the closing "Freshness" section out of the body — it
  was a research-methodology/sourcing log (when the teardown ran, which sources were re-fetched,
  what was deliberately cut), not an instruction for the agent building a chat shell. Every claim
  in the body already carries its own inline `[verified: source, date]` / `[observed N/4]` tag at
  its point of use, so no per-fact evidence was lost. Preserved below; nothing deleted.

  - Created 2026-07-29. Product observations are a four-way teardown of that date (ChatGPT Pro,
    Onyx v4.4.0, Claude, Gemini Ultra), recorded as neutral pattern description — no vendor assets
    or screenshots ship, because a screenshot freezes one day's UI and rots without saying so.
  - Primary sources, all re-fetched 2026-07-29 and quoted at their point of use in the body:
    `ai-sdk.dev/docs/ai-sdk-ui/chatbot-resume-streams`; help.openai.com article 20001246 plus
    release notes; the Onyx v4.4.0 source tree; help.openai.com "Projects in ChatGPT",
    support.claude.com "What are Projects", support.google.com/gemini/answer/13743730 — the three
    collaboration models, corrected: editors can invite, only removal is owner-restricted. ChatGPT
    group chats retired 2026-07-09.
  - Cut under the sourcing contract: the two exact canvas-removal dates (no primary source
    re-verified), and virtualization thresholds like "~100 messages" (no official source,
    in-thread territory anyway).

## [1.0.2] - 2026-07-31
### Changed
- Description reescrita para roteamento: triggers e anti-triggers explicitos (rodada 2, 2026-07-31).

## [1.0.1] - 2026-07-30
### Changed
- Distribution level flipped user->project (owner decision recorded in
  reports/level_flip_decisions.json): always-on discovery cost was not
  justified by measured stack reach; now installed only where the stack
  evidence exists.

