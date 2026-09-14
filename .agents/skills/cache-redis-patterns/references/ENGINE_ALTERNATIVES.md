# Redis-Compatible Cache Engines -- Alternatives, Cost, and Licensing

> Reference for the `cache-redis-patterns` skill.

Deep-dive on Redis alternatives, their trade-offs, ElastiCache cost/efficiency data, and the Redis 8+ licensing change that is material to the Valkey-vs-Redis decision. Read this when choosing a cache engine, comparing Valkey vs Redis on ElastiCache, or evaluating whether the Redis 8+ tri-license fits a distribution/SaaS model. All figures are perishable -- verify current pricing and benchmarks against the cited official sources.

---

## Alternatives to Redis

- **Valkey** 9.x (latest 9.1.0, 2026-05-19; verify official docs): BSD-licensed fork of Redis 7.2 (Linux Foundation). Swiss Tables-inspired hashtable. AWS now cites **up to ~40% memory efficiency** improvement for ElastiCache Valkey 8.x (e.g. SET uses ~24 fewer bytes per element in 8.0) and meaningful throughput gains over 7.2 (actual gains vary by workload; verify at https://valkey.io/blog/). Default on AWS ElastiCache for new clusters. Cost vs Redis OSS on ElastiCache: **node-based ~20% cheaper, Serverless ~33% cheaper**, combining to **up to ~60% total cost savings** (verify current pricing). Source: https://aws.amazon.com/blogs/database/reduce-your-amazon-elasticache-costs-by-up-to-60-with-valkey-and-cudos/
- **Dragonfly**: multi-threaded, Redis-compatible, claims 25x throughput of Redis on a single instance. Good for workloads that exceed single-threaded Redis capacity without clustering.
- **Garnet** (Microsoft): high-performance cache-store built on .NET, Redis RESP protocol compatible. Designed for extreme throughput on multi-core machines.
- **Memcached**: simple, mature, multi-threaded KV cache. No data structures beyond strings. Choose when you only need simple key-value caching without Redis features.
- **KeyDB**: multi-threaded Redis fork (Snap). Active replication, FLASH storage support.

---

## Licensing note (material to the Valkey-vs-Redis decision)

Redis 7.2 and earlier are BSD-licensed; **Redis 8+ Open Source is tri-licensed (AGPLv3 / RSALv2 / SSPLv1)**, and the bundled modules (RediSearch, RedisJSON, RedisTimeSeries, RedisBloom) ship under the same tri-license. Of the three, **only AGPLv3 is OSI-approved** (copyleft with a network/SaaS clause); RSALv2 and SSPLv1 are source-available, not OSI open source. Valkey remains BSD. Source: https://redis.io/blog/agplv3/

---

## Decision

- **Valkey** -- permissive open-source licensing (BSD) and multi-threaded performance; default on ElastiCache for new clusters.
- **Redis 8+** -- advanced modules (vector sets, time series, search, JSON), but confirm AGPLv3 / RSALv2 / SSPLv1 fits your distribution/SaaS model.
- **Dragonfly / Garnet** -- extreme single-node throughput.
- **Memcached** -- simple KV caching without data-structure needs.

---

**2026-07-28 re-check** (read this when you need the full licensing/version detail behind the SKILL.md summary): licensing facts above still hold -- Redis 8+ Open Source stays tri-licensed, the adopter picks **one** of RSALv2, SSPLv1, or AGPLv3, and RediSearch/RedisJSON/RedisTimeSeries/RedisBloom ship under the same tri-license; only AGPLv3 is OSI-approved, so Redis Ltd. markets Redis 8+ as "both source available and OSI-compliant open source" depending on the adopter's choice. No change since the March 2024 BSD-to-source-available split or the 2025 addition of the AGPLv3 option. Source: https://redis.io/legal/licenses/ (fetched 2026-07-28).

Redis patched to **8.8.1** (was 8.8): released 2026-07-23 with an explicit security fix -- "SECURITY: There is a security fix in the release" -- for crafted `RESTORE` payloads via the RedisBloom/TDigest modules that can trigger an out-of-bounds write. Upgrade to 8.8.1+ if you use RedisBloom or TDigest. Sources: https://github.com/redis/redis/releases/tag/8.8.1 and https://github.com/RedisBloom/RedisBloom/security/advisories (GHSA-7862-34pw-44wv covers the related, earlier May 2026 RESTORE/RedisBloom advisory; the 8.8.1 note additionally names TDigest).

Valkey still current at **9.1.0** (2026-05-19) -- no newer release found. Source: https://valkey.io/blog/

**2026-07-28 independent re-check**: re-fetched the 8.8.1 release notes directly. Severity is understated above -- the RedisBloom/RedisBloom#1044 advisory the release note points to describes the out-of-bounds write as **potentially leading to remote code execution**, not just memory corruption. Treat 8.8.1 as a P1 upgrade (RCE-class), not routine patch, if RedisBloom or TDigest is loaded. No other change to this file's facts. Source: https://github.com/redis/redis/releases/tag/8.8.1.
