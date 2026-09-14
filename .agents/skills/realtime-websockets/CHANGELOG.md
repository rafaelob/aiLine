# Changelog: realtime-websockets

All notable changes to this skill are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.1.5] - 2026-09-05
### Changed
- Added concise sibling boundaries to the activation description so adjacent skills route only when their own scope matches.

## [1.1.4] - 2026-09-05
### Changed
- Added conditional root routing and removed redundant first-level pairing prompts from the activation description; detailed material remains available through workflow-selected references.

## [1.1.3] - 2026-08-06
### Changed
- Moved the `## Freshness` section's dated audit trail out of `SKILL.md`'s body
  (provenance-out-of-body pass, per `AGENTS.md` §"O que vai dentro de um SKILL.md") and renamed
  the remaining fact-only block to `## Standards and library currency`, since it carries only live
  protocol/spec/library references and a reverify instruction, not a diary. Dates preserved:
  - **2026-07-28 — activation repair**: restored `rooms` and `reconnection` to the description
    (391 to 411 chars). The trim had dropped both even though Step 3 is entirely about room design
    and Step 5 entirely about reconnection, leaving those capabilities unreachable from the routing
    text. Recovers the `stuck-disconnected-after-deploy` and `pt-notificacoes-tempo-real` cases.
  - **2026-07-28 — version rot found and fixed**: WebTransport global browser support (caniuse)
    moved from ~80% (2026-06-04 check below) to 88.38% -- confirmed at
    https://caniuse.com/webtransport. Firefox for Android's first-supported version now reads 152
    (was 149 in the prior pass); Chrome for Android now shows 150. Updated both `SKILL.md` and
    `references/REALTIME_TRANSPORT_GUIDE.md` to match. W3C spec status unchanged: still Working
    Draft (dated 2026-07-06, confirmed at https://www.w3.org/TR/webtransport/).
  - **2026-07-28 — self-contradiction found and fixed**: the transport comparison table in
    `references/REALTIME_TRANSPORT_GUIDE.md` said WebTransport browser support was "Chrome, Edge,
    partial Firefox", omitting Safari entirely and downgrading Firefox from full to "partial",
    while `SKILL.md` already carried the specific, correct figures (Chrome 97+, Edge 98+, Firefox
    114+ full support, Safari 26.4+). Updated the reference table to match.
  - **2026-07-28 — re-verified, unchanged**: MQTT 5.0 still the current OASIS Standard (published
    2019-03-07, no MQTT 6 in development), Socket.IO npm latest 4.8.3 (not version-pinned in this
    skill, just linked), RFC 6455 (WebSocket) and RFC 7692 (permessage-deflate) still normative.
  - **2026-06-04 — original Freshness block**, superseded by the 2026-07-28 entries above where
    figures changed: WebSocket protocol RFC 6455 (per-message deflate RFC 7692); Server-Sent
    Events per the HTML Living Standard; WebTransport at ~80% global support (caniuse 80.35%,
    Chrome 97+, Edge 98+, Firefox 114+, Safari 26.4+), W3C spec in WD/CR, server-side support
    (aioquic, Node.js experimental, Deno/Bun) uneven; MQTT 5.0 OASIS Standard; links to Socket.IO,
    Centrifugo, SignalR, ws docs; instruction to confirm platform-specific connection limits (Cloud
    Run, AWS ALB, nginx, Cloudflare) in each provider's current docs.

## [1.1.2] - 2026-07-31
### Changed
- Description enxugada para o soft cap de 600 chars sem perder trigger nem anti-trigger (rodada 2, 2026-07-31).

## [1.1.1] - 2026-07-30
### Changed
- Distribution level flipped user->project (owner decision recorded in
  reports/level_flip_decisions.json): always-on discovery cost was not
  justified by measured stack reach; now installed only where the stack
  evidence exists.

## [1.1.0] - 2026-07-30
### Changed
- Description now carries the transport question in the words users use (the
  server only pushes to the client), auth on the connection handshake with an
  expiring token, fan-out across app instances, presence that must not show
  people online after a deploy, backpressure for a slow consumer, plus the PT-BR
  triggers "tempo real" / "reconexao" / "presenca". Tags went from 3 entries to
  the real vocabulary of the domain (`websocket`, `sse`, `mqtt`, `webtransport`,
  `handshake`, `presence`, `rooms`, `fan-out`, `reconnection`, `telemetry`, ...).
- Routing measurement: all 8 positive activation cases were green only on the
  `notes_contains` vote, scoring 0.000-0.214 (below the 0.30 threshold). They now
  score 0.300-0.700 on real overlap. No negative case regressed.

## [1.0.3] - 2026-07-28
### Changed
- Tightened description to <=400 chars (token-budget audit 2026-07-28); preserved use-for trigger and negative routing to graphql-realtime-subscriptions, game-dev-networking-multiplayer, notifications-omnichannel-delivery
