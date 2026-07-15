# Real-time Architecture

## Goal

Push card moves, edits, and comment creation to every connected client on a
board without requiring a manual refresh, and show which members are
currently viewing the board.

## Components

```text
Card mutation (service layer)
        ↓
Domain event object (card.moved, card.created, ...)
        ↓
Redis Pub/Sub channel: board:{board_id}:events
        ↓
EventBridge (subscribes per board, forwards to local ConnectionManager)
        ↓
ConnectionManager (in-process registry of WebSocket connections per board)
        ↓
All connected clients on that board receive the event
```

## ConnectionManager
- Keeps an in-memory mapping of `board_id -> set[WebSocket]`.
- One process may hold connections for many boards.
- Horizontal scaling works because the source of truth for broadcast is Redis Pub/Sub, not the in-memory map — any backend replica publishing an event reaches every replica’s connected clients, not just its own.

## Redis Pub/Sub bridge (EventBridge)
- On WebSocket connect for a board, the bridge subscribes to board:{board_id}:events if not already subscribed.
- On the last disconnect for a board, it unsubscribes to avoid leaking subscriptions.
- The service layer never talks to WebSockets directly — it returns/publishes domain events, and the router publishes to Redis after the DB commit succeeds. This avoids broadcasting an event for a mutation that was rolled back.

## Presence
- Presence is tracked with a Redis set per board (board:{board_id}:presence) plus a per-connection TTL heartbeat key.
- A connected client is considered “online” as long as its heartbeat key has not expired.
- Presence changes (presence.joined, presence.left) are broadcast the same way as card events, over the same per-board channel, but are filtered out on the frontend before triggering any data refetch.

## WebSocket auth handshake
- The client connects to /api/v1/ws/boards/{board_id}?token={access_token}.
- Token is validated the same way as REST requests (JWT decode + user lookup) before the connection is accepted.
- If the token is invalid, expired, or the user lacks board access, the server closes the connection with a policy-violation close code instead of accepting and closing later — this avoids a connect/immediate-disconnect flicker on the client.

## Event envelope

All events sent over the socket share a single shape:

```json
{
  "type": "card.moved",
  "board_id": "…",
  "actor_id": "…",
  "payload": { "...": "event-specific fields" }
}
```
`actor_id` lets clients ignore events they generated themselves (the client
already applied an optimistic update locally, so re-applying it via the
socket would be redundant and can cause visual flicker).

## Frontend
- `SocketClient` wraps the native `WebSocket`, exposing `connect()`, `close()`, and `onMessage()`, and handles reconnect with backoff.
- `useBoardSocket(boardId)` opens one connection per mounted board view, subscribes to messages, filters out the current user’s own events and presence events, and invalidates the relevant TanStack Query cache entry for anything else — triggering a refetch instead of manually patching cache state.

## Deliberate simplifications
- Card list refetch on remote events, rather than merging the event payload directly into cache. Simpler and consistent with TanStack Query’s invalidate-then-refetch model at this stage of the project.
- Presence UI (avatars) and reconnection UX polish are tracked separately and are not required for Day 6 completion per the roadmap.