# Messaging -- Pub/Sub and Streams Command Reference

> Reference for the `cache-redis-patterns` skill.

Raw command examples for the two Redis messaging primitives. Use Pub/Sub for ephemeral fire-and-forget broadcast; use Streams when you need persistence, consumer groups, acknowledgment, and replay. (A redis-py Streams consumer-group worker with `XAUTOCLAIM`-based dead-letter recovery is in `references/REDIS_PATTERNS_GUIDE.md`, section 5.)

---

## Pub/Sub (fire-and-forget)

No persistence; a message published while no subscriber is connected is lost. Good for real-time notifications and cache-invalidation broadcasts.

```
SUBSCRIBE channel:notifications
PUBLISH channel:notifications '{"type":"new_order","id":"o1"}'
```

---

## Redis Streams (reliable messaging)

Append-only log with consumer groups: each message is delivered to one consumer per group, must be acknowledged (`XACK`), and unacknowledged entries can be reclaimed after a timeout (`XAUTOCLAIM`) so a dead consumer's work is not lost.

```
-- Producer
XADD events * type order_created order_id o123

-- Consumer group
XGROUP CREATE events order-processors $ MKSTREAM
XREADGROUP GROUP order-processors worker-1 COUNT 10 BLOCK 2000 STREAMS events >

-- Acknowledge processed message
XACK events order-processors 1234567890-0

-- Claim stale messages (dead consumer recovery)
XAUTOCLAIM events order-processors worker-2 60000 0-0
```

---

## Streams vs Pub/Sub

- **Streams**: persistent, consumer groups, acknowledgment, replay. Choose when delivery must survive consumer downtime.
- **Pub/Sub**: ephemeral, broadcast, simpler. Choose for best-effort real-time fan-out where missed messages are acceptable.

Reference: https://redis.io/docs/latest/develop/data-types/streams/
