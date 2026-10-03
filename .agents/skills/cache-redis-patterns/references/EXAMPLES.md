# cache-redis-patterns examples

These examples are loaded only for the implementation path selected in the root skill.

## Example 1

Source section: ### Cache-aside (lazy loading)

```
Read: cache.get(key) -> hit? return : db.get -> cache.set(key, val, TTL) -> return
Write: db.write -> cache.delete(key)
```

## Example 2

Source section: ### Write-through

```
Write: cache.set(key, val) -> db.write (synchronous)
Read: cache.get(key) -> always hits (if key exists)
```

## Example 3

Source section: ### Write-behind (write-back)

```
Write: cache.set(key, val) -> queue for async db.write
Read: cache.get(key) -> always hits
```

## Example 4

Source section: ### Read-through

```
Read: cache.get(key) -> cache internally calls db.get on miss -> cache.set -> return
Write: db.write -> cache.delete(key) or cache.set(key, val)
```

## Example 5

Source section: ### Refresh-ahead (proactive)

```
Background: before TTL expires, async-refresh cache from DB
Read: cache.get(key) -> always hits (stale data briefly possible)
```

## Example 6

Source section: ### Layered caching (near-cache)

```
L1 (local, in-process): in-memory cache (Map, LRU cache) with short TTL (5-30s)
L2 (remote): Redis with longer TTL (minutes-hours)
Read: L1.get -> miss? -> L2.get -> miss? -> db.get -> set L2 -> set L1 -> return
Invalidation: Redis Pub/Sub to notify all instances to evict L1 keys
```

## Example 7

Source section: #### Server-assisted near-cache (RESP3 CLIENT TRACKING)

```
CLIENT TRACKING ON                          # default mode: server tracks keys this conn reads
CLIENT TRACKING ON BCAST PREFIX user:       # broadcast mode: invalidations by key prefix (no per-key memory)
CLIENT TRACKING ON OPTIN                    # only CACHING YES-flagged reads are tracked
# NOLOOP: do not notify the connection that made the write
```

## Example 8

Source section: ### Basic lock with SETNX

```
LOCK:   SET lock:resource $token NX PX 30000
UNLOCK: (Lua) if GET == $token then DEL
```

## Example 9

Source section: ## Step 6 -- Session storage

```python
# Key pattern: session:{session_id}
# Store as Hash for partial reads/updates
HSET session:abc123 user_id u1 role admin last_active 1709744400
EXPIRE session:abc123 1800  # 30 min TTL

# Extend on activity
EXPIRE session:abc123 1800  # reset TTL on each request
```

## Example 10

Source section: ### Tag-based invalidation

```
-- On write: track tagged keys
SADD tag:user:u1 "profile:u1" "orders:u1" "prefs:u1"

-- On invalidation: delete all tagged keys
SMEMBERS tag:user:u1 -> for each key: DEL key
DEL tag:user:u1
```

## Example 11

Source section: ### Redis Cluster

```
-- Force keys to same hash slot
SET {user:u1}:profile ...
SET {user:u1}:prefs ...
```

