# Rate Limiting -- Atomic Lua Scripts

> Reference for the `cache-redis-patterns` skill.

Atomic, server-side rate-limiting algorithms for Redis. Run each as a single `EVAL`/`EVALSHA` so the check-and-update is atomic (no race between concurrent clients). Pass the current time from the application (`ARGV` `now`) so the clock is consistent across nodes; do not rely on `TIME` inside the script if you need monotonic behavior across a cluster.

`KEYS[1]` is the per-subject rate-limit key. For multi-tenant isolation, prefix it: `ratelimit:{tenant_id}:{endpoint}`. Each script returns `1` (allowed) or `0` (denied).

---

## Token bucket (recommended default)

Smooths bursts: tokens refill continuously at `refill_rate` up to `max_tokens`; each request costs one token. Good general-purpose limiter that tolerates short bursts while bounding sustained rate.

- `ARGV[1]` `max_tokens` -- bucket capacity (max burst).
- `ARGV[2]` `refill_rate` -- tokens added per second (sustained rate).
- `ARGV[3]` `now` -- current time in seconds (from the app).

```lua
-- Lua script for atomic token bucket
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])  -- tokens per second
local now = tonumber(ARGV[3])

local data = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(data[1]) or max_tokens
local last_refill = tonumber(data[2]) or now

local elapsed = now - last_refill
tokens = math.min(max_tokens, tokens + elapsed * refill_rate)

if tokens >= 1 then
  tokens = tokens - 1
  redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
  redis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) + 1)
  return 1  -- allowed
else
  redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
  return 0  -- denied
end
```

---

## Sliding window counter

Exact request count within a rolling `window`, backed by a sorted set keyed on timestamp. More accurate than a fixed window (no boundary bursts) at the cost of storing one member per in-window request -- watch memory for very high-cardinality limits.

- `ARGV[1]` `window` -- window length in seconds.
- `ARGV[2]` `limit` -- max requests allowed within the window.
- `ARGV[3]` `now` -- current time in seconds (from the app).
- `ARGV[4]` `member` -- unique request ID (so concurrent requests at the same timestamp do not collide).

```lua
-- Sliding window using sorted set
local key = KEYS[1]
local window = tonumber(ARGV[1])  -- window in seconds
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local member = ARGV[4]  -- unique request ID

redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = redis.call('ZCARD', key)
if count < limit then
  redis.call('ZADD', key, now, member)
  redis.call('EXPIRE', key, window)
  return 1  -- allowed
end
return 0  -- denied
```

---

## Notes

- **Per-tenant rate limiting**: prefix the key with the tenant id, e.g. `ratelimit:{tenant_id}:{endpoint}`. The `{...}` hash tag also co-locates the key on one Cluster slot.
- **EXPIRE on the key** keeps idle limiters from leaking memory; both scripts above set it on every allowed write.
- **Choosing between them**: token bucket when you want burst tolerance and minimal per-key memory; sliding window counter when you need an exact count over a precise rolling interval.
