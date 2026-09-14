# Redis Patterns Quick Reference

> **Freshness disclaimer**: Written 2026-03. Verify against your Redis version and managed service documentation. Module availability (RedisJSON, RedisSearch) varies by provider.

## Official documentation

- Redis commands: https://redis.io/docs/latest/commands/
- Redis data types: https://redis.io/docs/latest/develop/data-types/
- Redis Streams: https://redis.io/docs/latest/develop/data-types/streams/
- Distributed locks: https://redis.io/docs/latest/develop/use/patterns/distributed-locks/

---

## 1. Caching Pattern Decision Matrix

```
Need consistency?
  Strong -> Write-through
  Eventual -> How stale is acceptable?
    Seconds -> Cache-aside with short TTL
    Minutes -> Cache-aside with longer TTL
    Zero-miss -> Refresh-ahead (proactive)

Write-heavy? YES -> Write-behind (async flush) | NO -> Cache-aside or write-through
Predictable access? YES -> Refresh-ahead | NO -> Cache-aside with stampede protection
```

---

## 2. Key Naming & TTL

```
Pattern: {service}:{entity}:{identifier}:{qualifier}
Examples: api:user:u123:profile | cache:product:p456:detail | lock:order:o789:process
```

Rules: colons as separators; prefix with service/purpose; use `{hash_tag}` for Cluster multi-key ops; keep keys short.

| Data | TTL | Rationale |
|------|-----|-----------|
| Session | 30 min | Security; extend on activity |
| User profile | 5-15 min | Changes infrequently |
| Product detail | 1-5 min | Moderate catalog updates |
| Rate limit window | Window size | Self-cleaning |
| Distributed lock | Operation timeout | Prevent deadlock |
| Search results | 30-60 sec | High cardinality |

**Jittered TTL** -- add `random(0, base_ttl * 0.1)` to prevent thundering herd.

---

## 3. Stampede Prevention

### Lock-based (single-flight)
```python
def get_with_lock(key, fetch_fn, ttl=3600):
    value = redis.get(key)
    if value: return value
    lock_key = f"lock:{key}"
    if redis.set(lock_key, "1", nx=True, ex=10):
        try:
            value = fetch_fn()
            redis.setex(key, ttl, value)
            return value
        finally:
            redis.delete(lock_key)
    else:
        time.sleep(0.1)
        return redis.get(key) or fetch_fn()
```

### Probabilistic early refresh (XFetch)
```python
def should_refresh(ttl_remaining, total_ttl, beta=1.0):
    if ttl_remaining <= 0: return True
    return random.random() < beta * math.exp(-ttl_remaining / (total_ttl * 0.1))
```

### Stale-while-revalidate
Store `fresh_until` and `stale_until` metadata alongside value. Return stale value immediately; trigger async refresh when past `fresh_until`.

---

## 4. Distributed Lock

```python
import uuid

def acquire_lock(redis, resource, ttl_ms=30000):
    token = str(uuid.uuid4())
    return token if redis.set(f"lock:{resource}", token, nx=True, px=ttl_ms) else None

# Atomic unlock via Lua (prevents releasing another's lock)
UNLOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) end
return 0
"""
def release_lock(redis, resource, token):
    redis.eval(UNLOCK_SCRIPT, 1, f"lock:{resource}", token)

# Extend lock for long operations (same Lua pattern with pexpire)
```

---

## 5. Redis Streams Consumer Group

```python
r = redis.Redis()
try: r.xgroup_create("orders", "processors", id="0", mkstream=True)
except redis.ResponseError: pass

while True:
    messages = r.xreadgroup("processors", "worker-1", {"orders": ">"}, count=10, block=5000)
    for stream, msgs in messages:
        for msg_id, data in msgs:
            try:
                process_order(data)
                r.xack("orders", "processors", msg_id)
            except Exception: pass  # Re-delivered after timeout

# Dead letter: claim messages pending > 5 minutes
stale = r.xautoclaim("orders", "processors", "worker-1", min_idle_time=300000, start_id="0-0")
```

---

## 6. Memory Management

| Policy | Behavior | Use case |
|--------|----------|----------|
| `noeviction` | Error on full | Queues, locks |
| `allkeys-lru` | Evict least recently used | General caching |
| `volatile-lru` | LRU among keys with TTL | Mixed cache + persistent |
| `allkeys-lfu` | Evict least frequently used | Frequency matters |
| `volatile-ttl` | Evict soonest-expiring | Sessions, temp data |

Monitor: `INFO memory` (used, peak, fragmentation ratio >1.5 = issue), `MEMORY USAGE key`, `MEMORY DOCTOR`.

### Encoding / listpack tuning (5-10x memory lever)

Small collections are stored in a compact `listpack` (older Redis: `ziplist`/`intset`) instead of a full `hashtable`/`skiplist`. Crossing a threshold permanently upgrades the key to the heavier encoding for its lifetime.

| Config | Default | Effect |
|--------|---------|--------|
| `hash-max-listpack-entries` / `hash-max-listpack-value` | 128 / 64 | Hash stays compact below both limits |
| `zset-max-listpack-entries` / `zset-max-listpack-value` | 128 / 64 | Sorted set stays compact |
| `list-max-listpack-size` | 128 | List node packing |
| `set-max-intset-entries` / `set-max-listpack-entries` | 512 / 128 | Int set / small string set compact |

```
OBJECT ENCODING myhash      # -> "listpack" (good) or "hashtable" (heavier)
MEMORY USAGE myhash         # bytes incl. overhead
redis-cli --bigkeys         # sample largest keys per type
```

**Bucket tiny String keys into Hashes**: instead of `user:1`, `user:2`, ... (each carries per-key dict + expire overhead), store `HSET users:bucket:{n} 1 ... 2 ...` with ~1000 fields/bucket so the hash stays in listpack encoding -- amortizes per-key overhead across many values. Raising thresholds (e.g. to 1024) trades CPU for less memory; lower them to favor CPU. Reference: https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/

---

## 7. Failure Handling

| Scenario | Response |
|----------|----------|
| Connection timeout | Retry with backoff (max 3); fallback to DB |
| Redis fully down | Serve from DB; degrade gracefully; alert |
| Memory full (noeviction) | Alert immediately; scale or evict |
| Network partition | Sentinel/Cluster promotes replica; risk of stale reads |
| Slow command (>10ms) | Check `SLOWLOG GET`; optimize structure or pipeline |

---

## 8. Server-assisted client-side caching (RESP3 CLIENT TRACKING)

A reliable L0 near-cache: the client keeps hot keys in process memory and Redis **pushes** an invalidation message when a tracked key changes, so the L0 is correct without polling or Pub/Sub plumbing. Hot reads skip the network entirely (up to ~45x faster). Requires a RESP3-capable client and `protocol 3` (HELLO 3).

```
CLIENT TRACKING ON                       # default: server remembers keys this conn read
CLIENT TRACKING ON BCAST PREFIX user:    # broadcast by prefix; no per-key server memory
CLIENT TRACKING ON OPTIN                 # only reads after `CACHING YES` are tracked
CLIENT TRACKING ON BCAST NOLOOP          # don't notify the connection that made the write
```

- **Default mode**: server stores the key->client map (uses server memory; freed via invalidation or eviction).
- **BCAST mode**: subscribe to key prefixes; no per-key server cost, but you get invalidations for keys you may not cache.
- **OPTIN / OPTOUT**: control which reads are tracked to bound cache size.
- **Connection pools**: data connections are shared, so route invalidation pushes to a dedicated connection with `CLIENT TRACKING ON REDIRECT <client-id>` (the redirect target is a connection in pub/sub mode listening on `__redis__:invalidate`).

```python
# redis-py (RESP3): enable client-side caching with a local cache
import redis
r = redis.Redis(protocol=3, cache_config=redis.cache.CacheConfig())
r.get("user:1")   # first read hits Redis; subsequent reads served from the local cache
r.get("user:1")   # local hit -- no round trip; auto-invalidated on server-side change
```

Client support: redis-py, Lettuce, Redisson, StackExchange.Redis (and others). Use it as the L0 in front of the L1/L2 layered pattern; cross-instance coherence still relies on the server-pushed invalidations rather than app-level Pub/Sub. Reference: https://redis.io/docs/latest/develop/reference/client-side-caching/
