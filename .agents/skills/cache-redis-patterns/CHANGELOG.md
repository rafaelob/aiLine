# Changelog — cache-redis-patterns

## [1.1.6] - 2026-09-05
### Changed
- Added concise sibling boundaries to the activation description so adjacent skills route only when their own scope matches.

## [1.1.5] - 2026-09-05
### Changed
Moved 11 implementation examples from the root into conditional references/EXAMPLES.md loading points while preserving their content.

## [1.1.4] - 2026-09-05
### Changed
- Added conditional root routing and removed redundant first-level pairing prompts from the activation description; detailed material remains available through workflow-selected references.

## [1.1.3] - 2026-08-06
### Changed
- Moved the `## Freshness` section's doc-link dump and dated verification log out of `SKILL.md`'s
  body (provenance-out-of-body pass, per `AGENTS.md` §"O que vai dentro de um SKILL.md"). Most of
  the links duplicated ones already cited inline in the body (client-side caching, memory
  optimization, pipelining, ElastiCache/Upstash pricing) or already consolidated into
  `references/DOC_LINKS.md`. The body now points to `references/DOC_LINKS.md` and
  `references/ENGINE_ALTERNATIVES.md` instead of repeating the links.
- **Renamed** the surviving `## Freshness` heading to `## Dependency Currency` -- the block that
  remains is a live fact (current Redis/Valkey versions and licensing) plus a reverify
  instruction, never a "last verified" diary entry, so the header should name what is under it,
  not the process that produced it.
- **Promoted** the Valkey module-parity caveat ("Valkey does not ship every Redis Stack module --
  confirm parity before recommending it for a workload that needs them") out of the Freshness
  diary and into the body's "Alternatives to Redis" list, next to the Decision guidance it
  actually qualifies.
- Backfilled, dates preserved -- these were dated log entries already in `SKILL.md`'s Freshness
  section, not previously recorded in this changelog:
  - **2026-06-29**: verified Redis Open Source current at 8.8 and Valkey at 9.1.0 (2026-05-19).
  - **2026-07-28 spot-check**: licensing unchanged (tri-license, only AGPLv3 OSI-approved) against
    https://redis.io/legal/licenses/; Redis patched to 8.8.1 with a security fix for crafted
    `RESTORE` payloads via RedisBloom/TDigest (detail already lived in
    `references/ENGINE_ALTERNATIVES.md`, unaffected by this change).

## [1.1.2] - 2026-07-30
### Changed
- Distribution level flipped user->project (owner decision recorded in
  reports/level_flip_decisions.json): always-on discovery cost was not
  justified by measured stack reach; now installed only where the stack
  evidence exists.
