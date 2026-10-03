# Redis references (official)

- Redis documentation: https://redis.io/docs/latest/
- Redis commands reference: https://redis.io/commands/
- Redis eviction policies: https://redis.io/docs/latest/develop/reference/eviction/
- Redis 8.x release notes: https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/
- Redis 8+ licensing (tri-license AGPLv3 / RSALv2 / SSPLv1; only AGPLv3 is OSI-approved): https://redis.io/blog/agplv3/ and https://redis.io/legal/licenses/
- Valkey documentation: https://valkey.io/docs/
- Valkey releases and blog: https://valkey.io/blog/
- Dragonfly: https://www.dragonflydb.io/docs
- Microsoft Garnet: https://microsoft.github.io/garnet/docs/
- Memcached: https://memcached.org/

## Version currency

Last verified 2026-07-28: Redis Open Source current is 8.8 (tri-licensed AGPLv3/RSALv2/SSPLv1,
only AGPLv3 OSI-approved); Valkey current is 9.1.0 (BSD). Re-verify both, and the GA/beta status of
Redis 8 vector sets and `HGETEX`/`MSETEX`, before relying on a version claim in `SKILL.md` or
`ENGINE_ALTERNATIVES.md`.
