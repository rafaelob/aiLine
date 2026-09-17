---
name: realtime-websockets
description: >-
  Real-time over WebSocket, SSE, WebTransport or MQTT: handshake auth,
  pub/sub fan-out, presence, backpressure, reconnection. Use for chat,
  dashboards, IoT; also "tempo real", "reconexao", "presenca". Pair with
  graphql-realtime-subscriptions and game-dev-networking-multiplayer.
license: Apache-2.0
metadata:
  author: coding-agent
  version: 1.1.5
  category: library-reference
  subcategory: api-reference
  vendor: universal
  lifecycle: active
  coding_agent: true
  tags:
  - realtime
  - websockets
  - websocket
  - sse
  - mqtt
  - webtransport
  - transport
  - protocol
  - client
  - server
  - connection
  - handshake
  - token
  - messages
  - instances
  - fan-out
  - pub-sub
  - presence
  - online
  - rooms
  - chat
  - notificacoes
  - usuarios
  - backpressure
  - memory
  - consumer
  - reconnection
  - deploy
  - telemetry
  - sensors
  - dashboard
  - collaboration
  - multiplayer
  - project_level
  audience: developer
  output_format: markdown
  modality: text
---

## Routing

Choose the smallest workflow that matches the request. Load a reference only when its topic is needed; otherwise use this root guide. Treat the workflow as a heuristic while preserving safety, protocol, schema, destructive-action, and artifact invariants. Provider/API facts remain where intrinsic to the named integration; executor or model choice does not change the contract.

# Real-Time Architecture (WebSockets / SSE / WebTransport)

Build low-latency real-time features (chat, live dashboards, notifications, collaboration) that scale, remain secure, and handle failure gracefully.

## Scope
- Adding real-time updates: notifications, live data feeds, collaborative editing.
- Choosing between WebSocket, SSE, and WebTransport for a use case.
- Designing pub/sub rooms, presence, and fan-out for multi-instance scaling.
- Hardening real-time endpoints: auth, rate limiting, reconnection, backpressure.
- Load testing WebSocket connections and message throughput.

## Inputs to collect
- Use case: chat, live metrics, notifications, collaboration, multiplayer -- determines transport.
- Direction: server-to-client only (SSE) or bidirectional (WebSocket/WebTransport).
- Scale: expected concurrent connections, messages per second, fan-out ratio.
- Deployment: single instance vs multi-instance; platform connection limits (Cloud Run, ELB, etc.).
- Ordering/delivery: are dropped messages acceptable, or is at-least-once required?

## Execution playbook

### Step 1 -- Choose the right transport
- **Server-Sent Events (SSE)**: server-to-client only, over HTTP/1.1 or HTTP/2. Simplest. Auto-reconnect built into browser `EventSource` API. Good for: notifications, live feeds, dashboards where client never sends data over the channel.
- **WebSocket**: full-duplex bidirectional over a persistent TCP connection. Good for: chat, collaborative editing, interactive features where both sides send messages. More complex: requires handshake upgrade, heartbeats, and reconnection logic.
- **WebTransport**: next-gen over HTTP/3 (QUIC). Supports reliable streams and unreliable datagrams. Good for: latency-sensitive applications (gaming, live video), when you need multiplexed streams without head-of-line blocking. Browser support is broad as of 2026-07 (~88% globally per caniuse, up from ~80% a month earlier): Chrome 97+, Edge 98+, Firefox 114+, Safari 26.4+, Chrome Android 150+, Samsung Internet 18+, Firefox Android 152+. W3C WebTransport spec is still in Working Draft/CR status -- server support (Node.js, Deno, Bun, Python aioquic) remains uneven. Keep a WebSocket fallback for older browsers and servers without HTTP/3.
- **MQTT 5.0**: lightweight pub/sub for IoT and constrained environments (OASIS Standard, current). 5.0 adds reason codes, user properties, shared subscriptions, and message expiry over 3.1.1. Good for: sensor data, device telemetry, low-bandwidth scenarios. Not browser-native but available via MQTT over WebSocket.
- Decision matrix:

  | Requirement | SSE | WebSocket | WebTransport |
  |-------------|-----|-----------|--------------|
  | Server -> Client only | Best | Overkill | Overkill |
  | Bidirectional | No | Yes | Yes |
  | Simple deployment (HTTP) | Yes | Needs upgrade | Needs HTTP/3 |
  | Auto-reconnect (browser) | Built-in | Manual | Manual |
  | Unreliable messages | No | No | Yes (datagrams) |
  | Multiplexed streams | No | No | Yes |
  | Browser support | Universal | Universal | ~88% (Chrome 97+, Edge 98+, Firefox 114+, Safari 26.4+) |
  | Compression | N/A | permessage-deflate | Built-in |

### Step 2 -- Design connection lifecycle and auth
- WebSocket lifecycle:
  1. Client connects with auth token in query param or first message (not in custom headers -- browsers do not support WS custom headers on upgrade).
  2. Server validates token; rejects with close code 4401 (unauthorized) or 4403 (forbidden).
  3. Server sends welcome message with connection ID and server time.
  4. Both sides exchange heartbeat pings (every 30s). If no pong within timeout (10s), close connection.
  5. On disconnect: client reconnects with exponential backoff + jitter.
- SSE lifecycle:
  1. Client sends GET with `Accept: text/event-stream` and auth via cookie or Bearer token header.
  2. Server validates auth and begins streaming events.
  3. Include `id:` field in events so the browser sends `Last-Event-ID` on reconnect.
  4. Browser `EventSource` auto-reconnects; server resumes from `Last-Event-ID`.
- Message envelope:
  ```json
  {
    "type": "order.status_changed",
    "version": 1,
    "id": "evt-abc-123",
    "timestamp": "2026-03-06T12:00:00Z",
    "data": { "order_id": "123", "status": "shipped" }
  }
  ```
- All message types and versions must be documented and validated on both sides.

### Step 3 -- Scale with pub/sub and fan-out
- Single instance: in-memory pub/sub (event emitter, channels) is sufficient.
- Multi-instance scaling:
  - Use Redis Pub/Sub, NATS, or a message broker as the fan-out backbone.
  - Each server instance subscribes to relevant channels/topics.
  - When a message is published, the broker fans it out to all instances; each instance delivers to its connected clients.
- Room/channel design:
  - Name rooms by resource: `order:123`, `user:456:notifications`, `dashboard:sales`.
  - Clients subscribe to rooms on connect; server validates access per room.
  - Track room membership per instance; clean up on disconnect.
- Presence:
  - Track online status per user across instances (Redis SET or sorted set with TTL).
  - Publish presence changes (join/leave) as events to the room.
  - Handle ghost presence: if a client disconnects without clean close, TTL expiry cleans up.
- Sticky sessions: some load balancers require session affinity for WebSocket. Use cookie-based or IP-hash affinity. Alternatively, use a stateless gateway pattern where any instance can serve any client (pub/sub handles fan-out).
- Self-hosted libraries and servers:
  - Socket.IO (Node.js): widely adopted, auto-fallback, rooms, namespaces, built-in reconnection
  - Centrifugo: language-agnostic real-time server (Go), WebSocket/SSE/SockJS, Redis/NATS/Kafka for scaling
  - SignalR (ASP.NET): .NET real-time framework, auto transport negotiation, Azure SignalR Service for managed scaling
  - ws (Node.js): minimal, standards-compliant WebSocket library
  - Soketi: open-source, Pusher-compatible WebSocket server (self-hosted drop-in replacement)
- Managed alternatives (when self-hosting is not justified):
  - Ably, Pusher, PubNub: managed real-time infrastructure with SDKs, presence, and channel management
  - Liveblocks: managed collaborative features (cursors, storage, comments)
  - AWS API Gateway WebSocket API: managed WebSocket endpoints, Lambda integration
  - Evaluate when: team lacks WebSocket operational experience, or scale requirements are unpredictable

### Step 4 -- Harden security and apply backpressure
- Origin validation: check `Origin` header on WebSocket upgrade; reject unknown origins.
- Rate limiting per connection: limit messages per second (e.g., 10 msg/s for chat). Drop or disconnect abusive clients.
- Message size limits: reject messages exceeding a maximum size (e.g., 64KB). Prevents memory exhaustion.
- Auth token refresh: for long-lived connections, require periodic re-authentication (send new token via the connection, or disconnect and reconnect with fresh token).
- Backpressure:
  - Monitor per-connection send buffer size. If a slow consumer's buffer grows beyond threshold, disconnect with a warning close code.
  - Server-side: use bounded queues per connection. Drop oldest messages or disconnect when full.
  - Client-side: if server is sending faster than client can process, signal backpressure or buffer with a cap.
- WebSocket compression: enable `permessage-deflate` extension for text-heavy payloads (chat, JSON). Reduces bandwidth 60-80% but adds CPU overhead. Disable for binary or already-compressed data.
- TLS: always use `wss://` (WebSocket over TLS) and `https://` (SSE) in production.
- CSRF: WebSocket upgrade is not protected by SameSite cookies. Validate origin header.

### Step 5 -- Implement client resilience and testing
- Reconnection strategy:
  - Exponential backoff: 1s, 2s, 4s, 8s, ... up to 30s max.
  - Add jitter: `delay = min(base * 2^attempt, max) * (0.5 + random * 0.5)`.
  - On reconnect, re-subscribe to rooms and request missed messages (using last event ID or sequence number).
- Message buffering: buffer outgoing messages during disconnection; replay on reconnect (bounded buffer, discard oldest if full).
- Offline indicator: show connection status to user; indicate when operating on stale data.
- Testing:
  - Unit test message serialization/deserialization and business logic.
  - Integration test: connect a WebSocket/SSE test client, send messages, verify delivery. Use framework-native test clients (e.g., FastAPI `WebSocketTestSession`, `httpx` for SSE).
  - Load test: use tools like `k6` (WebSocket support), `artillery`, or `locust` to simulate concurrent connections and message throughput. Measure: connection time, message latency p50/p95/p99, memory per connection, max concurrent connections.
  - Chaos test: simulate network partitions, server restarts, and slow consumers to verify reconnection and backpressure behavior.

## Deliverables / Definition of Done
- Transport choice (SSE/WebSocket/WebTransport) is documented with rationale.
- Connection lifecycle includes auth, heartbeats, and reconnection with backoff.
- Multi-instance scaling uses pub/sub fan-out; rooms and presence work across instances.
- Security: origin validation, rate limiting, message size limits, TLS enforced.
- Load tests demonstrate acceptable performance at expected concurrency.

## Common pitfalls / gotchas
- No heartbeats: dead connections consume resources indefinitely.
- No backpressure: slow consumers cause server memory exhaustion.
- Auth only at connection time: long-lived connections outlive token expiry without re-auth.
- Using WebSocket when SSE would suffice: unnecessary complexity for server-to-client streams.
- Not testing reconnection: clients get stuck in a disconnected state after server restarts.

## Example prompts
- "Implement SSE-based live notifications with last-event-ID resumption."
- "Add WebSocket chat with rooms, presence, Redis pub/sub, and reconnection."
- "Load test our WebSocket endpoint for 10k concurrent connections with k6."

## Reference files

- [`references/REALTIME_TRANSPORT_GUIDE.md`](references/REALTIME_TRANSPORT_GUIDE.md) -- Read when you need the close-code table, lifecycle ASCII diagrams, Redis room/presence code, the reconnection class, or the k6 load-test script.

## Invocation
- Prefer implicit selection.
- To explicitly request: **Use the `realtime-websockets` skill**.

## Standards and library currency

WebSocket protocol is RFC 6455 (https://www.rfc-editor.org/rfc/rfc6455, still normative) with
per-message deflate RFC 7692. Server-Sent Events is defined by the HTML Living Standard
(https://html.spec.whatwg.org/multipage/server-sent-events.html). WebTransport is still a W3C
Working Draft (https://www.w3.org/TR/webtransport/); check current browser support at
https://caniuse.com/webtransport before relying on the percentage in Step 1 -- it moves fast and
server-side support (aioquic, Node.js, Deno/Bun) remains uneven, so keep a WebSocket fallback. MQTT
5.0 is the current OASIS Standard (https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html), no
MQTT 6 in development. Library docs: Socket.IO (https://socket.io/docs/), Centrifugo
(https://centrifugal.dev/docs/), SignalR (https://learn.microsoft.com/en-us/aspnet/core/signalr/),
ws (https://github.com/websockets/ws).

Confirm platform-specific connection limits (Cloud Run, AWS ALB, nginx, Cloudflare) in each
provider's current docs before relying on them; serverless platforms vary widely on long-lived
connection support. See `CHANGELOG.md` for the dated verification history.
