---
name: cache-redis-patterns
description: >-
  Redis caching and coordination: cache-aside, TTL jitter, stampede protection,
  rate limits, Redlock, Streams, Pub/Sub. Use when adding hot-path cache, locks,
  or Redis messaging. Pair with background-jobs-queues for durable jobs and
  realtime-websockets for transport.
license: Apache-2.0
metadata:
  author: coding-agent
  version: 1.1.6
  category: library-reference
  subcategory: api-reference
  vendor: universal
  lifecycle: active
  coding_agent: true
  tags:
  - library-reference
  - cache
  - redis
  - cache-aside
  - distributed-locking
  - rate-limiting
  - project_level
  audience: developer
  output_format: markdown
  modality: text
---

## Routing

Choose the smallest workflow that matches the request. Load a reference only when its topic is needed; otherwise use this root guide. Treat the workflow as a heuristic while preserving safety, protocol, schema, destructive-action, and artifact invariants. Provider/API facts remain where intrinsic to the named integration; executor or model choice does not change the contract.

# Caching and Coordination Patterns

Production playbook for caching strategies, data structure selection, rate limiting, distributed locks, messaging, and cluster operations. This skill teaches **patterns first** (cache-aside, write-through, stampede protection, distributed locking) and uses Redis as the primary implementation reference, with alternatives noted throughout.

## Scope

- Adding caching to reduce latency/cost on hot paths.
- Implementing rate limiting, request shaping, or quotas.
- Using Redis for session storage, leaderboards, or real-time counters.
- Coordinating distributed work (locks, leader election).
- Building real-time messaging or event streaming.

## Inputs to collect (ask only if missing / blocking)

- Redis deployment: managed (ElastiCache, Memorystore, Upstash, Redis Cloud) vs self-hosted.
- Redis version and available modules (RedisJSON, RedisSearch, etc.).
- Consistency requirements: how stale can cached data be?
- Keyspace constraints: multi-tenant, per-environment prefixes.
- Expected QPS, payload sizes, and memory budget.

## Step 1 -- Caching patterns

### Cache-aside (lazy loading)

See references/EXAMPLES.md, Example 1, for this implementation path.

- Most common pattern. Application manages cache explicitly.
- Risk: cache miss storm on cold start or mass invalidation.
- Mitigation: warm cache on deploy; use jittered TTLs.

### Write-through

See references/EXAMPLES.md, Example 2, for this implementation path.

- Guarantees cache consistency with DB.
- Higher write latency (cache + DB in write path).
- Good for read-heavy workloads with strong consistency needs.

### Write-behind (write-back)

See references/EXAMPLES.md, Example 3, for this implementation path.

- Lowest write latency. Risk of data loss if Redis crashes before flush.
- Requires reliable flush mechanism (Redis Streams or external queue).
- Good for counters, analytics, non-critical state.

### Read-through

See references/EXAMPLES.md, Example 4, for this implementation path.

- Cache manages its own data loading (application does not manage cache explicitly).
- Requires a cache loader/provider function or library support.
- Simplifies application code; cache handles miss logic.

### Refresh-ahead (proactive)

See references/EXAMPLES.md, Example 5, for this implementation path.

- Eliminates cache miss latency for predictable keys.
- Implement with sorted set of expiry times + background worker.

### Layered caching (near-cache)

See references/EXAMPLES.md, Example 6, for this implementation path.

- Sub-millisecond reads from L1; L2 as shared fallback.
- Use for extremely hot paths (session lookups, feature flags, config).
- Invalidation via Redis Pub/Sub ensures L1 caches stay coherent across instances.

#### Server-assisted near-cache (RESP3 CLIENT TRACKING)

Prefer **server-assisted client-side caching** over a Pub/Sub-driven L1 when the client and library support RESP3 -- Redis pushes invalidation messages itself, so the L1 is reliably invalidated (unlike RESP2/keyspace-notification near-caches) and hot reads skip the network round trip entirely (up to ~45x faster reads).

See references/EXAMPLES.md, Example 7, for this implementation path.

- **Default tracking** uses server-side memory to remember keys; **BCAST** scales to many keys by prefix with no per-key server cost.
- For connection pools, use the **redirect** option to push invalidations to a second (pub/sub) connection (`CLIENT TRACKING ON REDIRECT <client-id>`), since the data connections are shared.
- Client support: redis-py, Lettuce, Redisson, StackExchange.Redis (and others). Complements the L1/Pub-Sub layered pattern above rather than replacing the cross-instance coherence story.
- Detail and a Python sketch: see [references/REDIS_PATTERNS_GUIDE.md](references/REDIS_PATTERNS_GUIDE.md) section 8.
- Reference: https://redis.io/docs/latest/develop/reference/client-side-caching/

## Step 2 -- Data structure selection

| Structure | Use case | Key operations |
|-----------|----------|----------------|
| **String** | Simple K/V, counters, flags | `SET`, `GET`, `INCR`, `SETNX` |
| **Hash** | Object storage, partial updates | `HSET`, `HGET`, `HMGET`, `HINCRBY` |
| **List** | Queues, recent items, activity feeds | `LPUSH`, `RPOP`, `LRANGE`, `LTRIM` |
| **Set** | Tags, unique membership, intersections | `SADD`, `SISMEMBER`, `SINTER`, `SUNION` |
| **Sorted Set** | Leaderboards, priority queues, time-series | `ZADD`, `ZRANGE`, `ZRANGEBYSCORE`, `ZRANK` |
| **Stream** | Event log, reliable messaging, consumer groups | `XADD`, `XREAD`, `XREADGROUP`, `XACK` |
| **JSON** (RedisJSON) | Complex nested documents | `JSON.SET`, `JSON.GET`, `JSON.ARRAPPEND` |
| **Vector Set** (Redis 8+, beta/preview) | Semantic search, embeddings, similarity | `VADD`, `VSIM`, `VREM` |

### Redis 8.x new commands

- **HGETEX / HSETEX** (Redis 8.0+): get/set hash fields with per-field TTL -- simplifies session and cache patterns.
- **MSETEX** (Redis 8.4+): set multiple keys with TTL in a single atomic operation.
- **Atomic compare-and-set**: `SET` command now supports CAS for lock-free concurrency patterns.
- **XACKDEL**: acknowledge and delete stream entries atomically.
- **Vector sets** (Redis 8+, beta/preview -- verify GA status at https://redis.io/docs/): native vector embeddings for semantic search.

### Choosing between Hash and JSON

- **Hash**: flat key-value pairs; native Redis; no module needed. Use HGETEX/HSETEX (Redis 8+) for per-field expiry.
- **JSON**: nested objects, arrays, atomic path updates; built into Redis 8+ (no separate module needed).
- Rule: use Hash for simple objects; JSON for nested structures.

### Memory-efficiency levers (the biggest low-effort cost reducer)

Encoding choice often shrinks cluster sizing more than any pattern change -- collections kept under their **listpack** thresholds use ~5-10x less memory than the `hashtable`/`skiplist` encodings.

- Keep collections under the listpack limits: `hash-max-listpack-entries` 512 / `hash-max-listpack-value` 64 (and the `zset-`, `list-`, `set-max-listpack-*` / `set-max-intset-entries` equivalents). Crossing a threshold permanently converts the key to the heavier encoding.
- **Bucket many small String keys into Hashes** (e.g. ~1000 fields per hash) to amortize the ~per-key overhead -- a large win when you have millions of tiny keys.
- Tune for your workload: raising thresholds (e.g. to 1024) trades CPU for lower memory; lowering them trades memory for CPU.
- Diagnose: `OBJECT ENCODING key` (confirm `listpack`/`intset` vs `hashtable`/`skiplist`), `MEMORY USAGE key`, and `redis-cli --bigkeys` to find offenders.
- Detail and examples: see [references/REDIS_PATTERNS_GUIDE.md](references/REDIS_PATTERNS_GUIDE.md) section 6.
- Reference: https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/

### Pipelining and batching (collapse round trips)

Cache latency is usually dominated by network RTT, not Redis CPU. Collapse N sequential commands into one round trip with **pipelining** or multi-key commands (`MGET`/`MSET`/`HMGET`). This is also a direct cost lever on per-request-billed services (Upstash, ElastiCache Serverless) -- fewer billed commands. Caution: do not build pipelines so large they monopolize the single event loop or balloon client/server memory; batch in bounded chunks. Reference: https://redis.io/docs/latest/develop/use/pipelining/

## Step 3 -- Rate limiting

Run the limiter as one atomic Lua `EVAL`/`EVALSHA` (no cross-client race); pass `now` from the app.

- **Token bucket (recommended default)**: continuous refill up to a cap, one token per request -- tolerates bursts, bounds sustained rate, minimal per-key memory.
- **Sliding window counter**: exact count over a rolling window via a sorted set (no fixed-window boundary bursts), one member per in-window request.

**Per-tenant rate limiting**: prefix key with tenant_id, `ratelimit:{tenant_id}:{endpoint}` (the `{...}` hash tag also co-locates the key on one Cluster slot).

Full Lua scripts + argument layouts: see [references/RATE_LIMITING_LUA.md](references/RATE_LIMITING_LUA.md).

## Step 4 -- Distributed locking

### Basic lock with SETNX

See references/EXAMPLES.md, Example 8, for this implementation path.

**Critical rules:**
- Always set expiry (PX) to prevent deadlocks.
- Use unique token (UUID) to prevent releasing another client's lock.
- Keep critical sections short (< lock TTL).

### Redlock algorithm (multi-node)

For higher reliability across independent Redis instances:
1. Acquire lock on N/2+1 independent Redis nodes.
2. Measure elapsed time; lock is valid only if acquired within TTL.
3. If failed: release on all nodes.

**Fencing tokens**: For safety-critical operations, use monotonically increasing fencing tokens validated by the resource being protected.

**Warning**: Redlock has known limitations in async/partitioned environments. For strict mutual exclusion, prefer Zookeeper/etcd.

## Step 5 -- Pub/Sub and Redis Streams

- **Pub/Sub (fire-and-forget)**: ephemeral broadcast, no persistence -- missed messages are lost. Good for real-time notifications and cache-invalidation broadcasts.
- **Redis Streams (reliable messaging)**: persistent append-only log with consumer groups, acknowledgment (`XACK`), replay, and dead-consumer recovery (`XAUTOCLAIM`). Choose when delivery must survive consumer downtime.

Raw command examples (`SUBSCRIBE`/`PUBLISH`, `XADD`/`XGROUP`/`XREADGROUP`/`XACK`/`XAUTOCLAIM`): use [references/MESSAGING_COMMANDS.md](references/MESSAGING_COMMANDS.md). A redis-py consumer-group worker is in [references/REDIS_PATTERNS_GUIDE.md](references/REDIS_PATTERNS_GUIDE.md) section 5.

## Step 6 -- Session storage

See references/EXAMPLES.md, Example 9, for this implementation path.

**Best practices:**
- Serialize minimal data (user_id, role, tenant_id) -- not full user object.
- Use consistent TTL aligned with application session timeout.
- Eviction policy: `volatile-ttl` or `volatile-lru` to protect non-session keys.

## Step 7 -- Cache invalidation strategies

| Strategy | Mechanism | Best for |
|----------|-----------|----------|
| **TTL expiration** | `EXPIRE key seconds` | Time-bounded staleness acceptable |
| **Event-driven** | Delete on write/webhook | Strong consistency needs |
| **Tag-based** | Set of keys per tag; delete all on tag invalidation | Multi-key invalidation (e.g., user's caches) |
| **Version-based** | Key includes version: `product:v3:123` | Deploy-time cache bust |

### Tag-based invalidation

See references/EXAMPLES.md, Example 10, for this implementation path.

### Stampede protection

- **Single-flight / lock**: Only one request refreshes; others wait or get stale.
- **Probabilistic early refresh**: Refresh randomly before TTL with probability increasing as expiry approaches.
- **Stale-while-revalidate**: Serve stale value; async refresh in background.

## Step 8 -- Clustering and high availability

### Redis Cluster

- Data sharded across nodes using hash slots (0-16383).
- Multi-key operations only work within same hash slot (use `{hash_tag}`).
- Minimum: 3 masters + 3 replicas.

See references/EXAMPLES.md, Example 11, for this implementation path.

### Redis Sentinel (HA without sharding)

- Monitors master; automatic failover to replica.
- Good for single-shard deployments that need HA.
- Application connects via Sentinel for master discovery.

### Managed service considerations

| Provider | Clustering | Notes |
|----------|-----------|-------|
| **ElastiCache** | Cluster mode enabled | Auto-failover, encryption at rest; defaults to Valkey for new clusters |
| **Memorystore** | Standard/Basic tier | No cluster mode; use replica for HA |
| **Upstash** | Serverless | Per-request pricing; auto-scaling; scales to zero |
| **Redis Cloud** | Active-Active | Multi-region, CRDT-based |

**Per-request vs provisioned crossover** (verify current pricing): per-request/serverless (Upstash PAYG, ElastiCache Serverless) bills by commands + stored GB and **scales to zero**, so it is cheaper for spiky, edge, or low/idle traffic; fixed/provisioned nodes win for steady high QPS. Rough break-evens: Upstash PAYG (~$0.20 / 100k commands + ~$0.25 / GB-month) crosses its fixed plans around ~10M commands/month; ElastiCache Serverless floors near ~$6/month for Valkey (100 MB/hr min) vs ~$60/month for a comparable Redis OSS minimum, and scales to ~5M RPS. Because per-request bills per command, **pipelining/MGET to collapse commands cuts the bill directly**. Sources: https://upstash.com/docs/redis/overall/pricing and https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/serverless-overview.html

### Alternatives to Redis

- **Valkey** 9.x (latest 9.1.0, 2026-05) -- BSD-licensed Redis 7.2 fork (Linux Foundation); 9.x adds hash field expiry in cluster mode, atomic slot migrations, sub-ms latency at 1B ops/sec per cluster; ElastiCache cites up to ~40% memory efficiency and up to ~60% cost savings vs Redis OSS; default on ElastiCache for new clusters.
- **Dragonfly** -- multi-threaded, Redis-compatible, ~25x single-instance throughput.
- **Garnet** (Microsoft) -- .NET RESP-compatible cache-store for extreme multi-core throughput.
- **Memcached** -- simple multi-threaded KV cache, strings only, no Redis data structures.
- **KeyDB** -- multi-threaded Redis fork; active replication, FLASH storage.

**Module parity gap**: Valkey does not ship every Redis Stack module (e.g., time series, vector sets) -- confirm parity before recommending it for a workload that needs them.

**Licensing**: Redis 7.2 and earlier are BSD; **Redis 8+ Open Source is tri-licensed (AGPLv3 / RSALv2 / SSPLv1)** (modules included) -- only AGPLv3 is OSI-approved. Valkey remains BSD.

**Decision**: Valkey for permissive (BSD) open source + multi-threaded performance; Redis 8+ for advanced modules (vector sets, time series, search, JSON) if its tri-license fits your distribution/SaaS model; Dragonfly/Garnet for extreme single-node throughput; Memcached for simple KV. Detailed efficiency/cost figures, sources, and the full licensing breakdown: read [references/ENGINE_ALTERNATIVES.md](references/ENGINE_ALTERNATIVES.md).

## Deliverables / Definition of Done

- [ ] Cache hit ratio measured and tracked (target > 95% for hot paths).
- [ ] TTLs use jitter (e.g., TTL + random(0, TTL*0.1)) to avoid thundering herd.
- [ ] Redis/cache failure is handled gracefully (fallback to source of truth, no crash).
- [ ] Rate limiting is tenant-aware with appropriate key prefixes.
- [ ] Lock TTLs are shorter than operation timeout.
- [ ] Memory usage monitored; eviction policy configured.
- [ ] Keyspace naming convention documented.

## Common pitfalls

- No TTL jitter -- mass expiration causes thundering herd (cache stampede).
- Treating cache as source of truth -- data loss on eviction or restart.
- No fallback on cache failure -- application crashes instead of falling back to DB.
- Unbounded memory without eviction policy -- OOM kills the Redis process.
- Using Redlock for strict mutual exclusion in partitioned environments -- use etcd/ZooKeeper instead.
- Storing large objects (> 100 KB) in Redis -- increases latency and memory pressure.
- No key naming convention -- key collisions across services or tenants.
- Cache warming not planned -- cold start after deploy causes DB load spike.

## Example prompts

- "Design a cache-aside pattern with stampede protection for our product catalog API."
- "Implement token-bucket rate limiting with Redis Lua scripts for our multi-tenant API."
- "Set up Redis Cluster with hash tags for co-locating user session and preference keys."
- "Compare Valkey vs Redis for our ElastiCache deployment -- we need BSD licensing and low memory overhead."

## References

- [references/REDIS_PATTERNS_GUIDE.md](references/REDIS_PATTERNS_GUIDE.md) -- read for caching patterns, data structures, memory tuning, distributed locks, streams, and client-side caching.
- [references/RATE_LIMITING_LUA.md](references/RATE_LIMITING_LUA.md) -- use when implementing the token-bucket or sliding-window Lua rate limiters (full scripts + argument layouts).
- [references/MESSAGING_COMMANDS.md](references/MESSAGING_COMMANDS.md) -- read when wiring Pub/Sub or Streams (raw `SUBSCRIBE`/`PUBLISH` and `XADD`/`XREADGROUP`/`XACK`/`XAUTOCLAIM` examples).
- [references/ENGINE_ALTERNATIVES.md](references/ENGINE_ALTERNATIVES.md) -- read when choosing a cache engine (Valkey/Dragonfly/Garnet/Memcached/KeyDB), comparing ElastiCache cost/efficiency, or evaluating the Redis 8+ tri-license.
- [`references/DOC_LINKS.md`](references/DOC_LINKS.md) -- see for official Redis documentation links.

## Invocation

- Prefer implicit selection.
- To explicitly request this skill, say: **Use the `cache-redis-patterns` skill**.

## Dependency Currency

Redis/Valkey current versions, licensing terms, and module GA/beta status (e.g. Redis 8 vector sets, `HGETEX`/`MSETEX`) are perishable -- reverify against [`references/DOC_LINKS.md`](references/DOC_LINKS.md) before relying on a version or licensing claim, and against [`references/ENGINE_ALTERNATIVES.md`](references/ENGINE_ALTERNATIVES.md) before recommending an engine on cost or module-parity grounds.
