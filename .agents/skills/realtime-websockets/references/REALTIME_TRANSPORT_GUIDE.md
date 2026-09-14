<!-- FRESHNESS: Always verify against official docs. Links may change. Last structured: 2026-07 -->

# Real-Time Transport Guide

Quick-reference for WebSocket, SSE, and WebTransport lifecycle, scaling, and patterns.

## Transport Comparison

| Feature | SSE | WebSocket | WebTransport |
|---------|-----|-----------|--------------|
| Direction | Server -> Client | Bidirectional | Bidirectional |
| Protocol | HTTP/1.1 or HTTP/2 | TCP (HTTP upgrade) | HTTP/3 (QUIC) |
| Auto-reconnect | Built-in (browser) | Manual | Manual |
| Binary data | No (text only) | Yes | Yes |
| Multiplexing | Via HTTP/2 | No (one stream) | Yes (multi-stream) |
| Unreliable channel | No | No | Yes (datagrams) |
| Proxy friendly | Yes (HTTP) | Needs upgrade | Needs HTTP/3 |
| Browser support | Universal | Universal | ~88% global (Chrome 97+, Edge 98+, Firefox 114+ full, Safari 26.4+); verify at caniuse.com/webtransport |

## WebSocket Lifecycle

```
Client                          Server
  |-- GET /ws?token=xxx -------->|  Upgrade: websocket
  |<-- 101 Switching Protocols --|  (or close 4401 on auth fail)
  |<-- {"type":"welcome"} ------|
  |<-- ping ---------------------|  (every 30s)
  |-- pong --------------------->|
  |-- subscribe(room) --------->|
  |<-- event data ---------------|
  |-- close(1000) ------------->|  (normal close)
```

### Close Codes

| Code | Meaning | Action |
|------|---------|--------|
| 1000 | Normal closure | Clean disconnect |
| 1001 | Going away (shutdown) | Reconnect |
| 1006 | Abnormal (no close frame) | Reconnect |
| 1008 | Policy violation | Do not reconnect |
| 1011 | Server error | Reconnect with backoff |
| 4401 | Unauthorized (custom) | Re-authenticate then reconnect |
| 4429 | Rate limited (custom) | Reconnect with longer backoff |

## SSE Lifecycle

```
Client                           Server
  |-- GET /events               |  Accept: text/event-stream
  |<-- 200 OK ------------------|  Content-Type: text/event-stream
  |<-- id: 1                ----|  event: order.updated
  |    data: {"order_id":"123"} |
  |   (connection drops)         |
  |-- GET /events               |  (auto-reconnect)
  |   Last-Event-ID: 1          |  (resume from last ID)
```

Event fields: `id` (for resumption), `event` (type), `data` (payload, multi-line OK), `retry` (reconnect delay ms). Empty line terminates event.

## Scaling Patterns

### Redis Pub/Sub Fan-Out
```
[Publisher] -> PUBLISH order:123 '{...}' -> [Redis]
  +-- [Server 1] subscribes -> Client A, Client B
  +-- [Server 2] subscribes -> Client C
```
All clients receive the event regardless of which instance they connect to.

### Room/Channel Management
```python
rooms: dict[str, set[Connection]] = defaultdict(set)

async def join_room(conn, room):
    if not await authorize(conn.user, room):
        return await conn.send_error("FORBIDDEN")
    rooms[room].add(conn)
    await redis.subscribe(room, handler=lambda msg: deliver(room, msg))

async def leave_room(conn, room):
    rooms[room].discard(conn)
    if not rooms[room]:
        await redis.unsubscribe(room)
```

### Presence Tracking
Redis sorted set with `score = last_seen_timestamp`. Query online users via `ZRANGEBYSCORE` with cutoff. Periodic cleanup removes entries stale >2 minutes.

## Reconnection Strategy

```python
class ReconnectingWebSocket:
    def __init__(self, url):
        self.url = url
        self.attempt = 0
        self.max_delay = 30.0
        self.base_delay = 1.0
        self.buffer: list = []  # Bounded (max 100)

    def get_delay(self) -> float:
        delay = min(self.base_delay * (2 ** self.attempt), self.max_delay)
        jitter = delay * (0.5 + random.random() * 0.5)
        self.attempt += 1
        return jitter

    async def on_open(self):
        self.attempt = 0
        for room in self.subscriptions:
            await self.subscribe(room)
        while self.buffer:
            await self.send(self.buffer.pop(0))

    async def on_close(self):
        await asyncio.sleep(self.get_delay())
        await self.connect()
```

## Security Checklist

| Control | Implementation |
|---------|---------------|
| Authentication | Token in query param (WS) or header (SSE) on connect |
| Re-authentication | Fresh token every N minutes for long-lived connections |
| Origin validation | Check `Origin` header; reject unknown origins |
| Rate limiting | Per-connection message rate limit (e.g., 10 msg/s) |
| Message size limit | Reject > max size (e.g., 64KB) |
| Room authorization | Validate access on every subscribe/join |
| TLS | Always `wss://` / `https://` in production |
| Input validation | Validate incoming messages against schema |
| Backpressure | Disconnect slow consumers when buffer exceeds threshold |

## Load Testing (k6)

```javascript
import { WebSocket } from 'k6/websockets';
import { check } from 'k6';
export const options = {
  stages: [
    { duration: '30s', target: 1000 },
    { duration: '2m', target: 1000 },
    { duration: '30s', target: 0 },
  ],
};
export default function () {
  const ws = new WebSocket('wss://api.example.com/ws?token=test');
  ws.onopen = () => {
    check(ws, { 'Connected': (s) => s.readyState === 1 });
    ws.send(JSON.stringify({ type: 'subscribe', room: 'test' }));
    setTimeout(() => ws.close(), 120000);
  };
  ws.onerror = (e) => { if (e.error != undefined) check(e, { 'No error': () => false }); };
}
```

**Metrics to measure:** connection establishment (p50/p95/p99), message delivery latency, memory per connection, max concurrent connections, reconnection storm behavior.

## References

- WebSocket API: https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API
- SSE: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- WebTransport: https://developer.mozilla.org/en-US/docs/Web/API/WebTransport
- RFC 6455: https://www.rfc-editor.org/rfc/rfc6455
- k6 WebSocket: https://grafana.com/docs/k6/latest/javascript-api/k6-ws/
- Socket.IO: https://socket.io/docs/
