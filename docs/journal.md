## Phase: Kanban UI and Drag & Drop (Frontend)

### Scope
- Kanban board, columns, and card components using @dnd-kit
- Optimistic reordering with client-side LexoRank
- Persistence of moves through CardService
- Card modal exposing title, description, priority, due date, checklist, labels, and assignees
- TanStack Query for board caching and invalidation

### Design decisions
- Optimistic updates apply moves locally before the server responds, then reconcile
  through query invalidation in onSettled.
- LexoRank is computed on the client using the same algorithm as the backend so that
  the optimistic order matches persisted order.
- @dnd-kit was chosen over react-beautiful-dnd for active maintenance, accessibility,
  and better TypeScript support.
- The board is fetched as a single aggregate (columns with nested cards) to avoid
  N+1 client fetches; TanStack Query caches it under a board-scoped key.

### Testing
- Unit test for the optimistic move reducer (applyMove).
- Unit test for the LexoRank between-helper.
- Component test for column rendering and card creation.

### Follow-ups
- Wire checklist, label, and assignee mutations in the card modal.
- Replace REST refetch-on-settle with real-time WebSocket updates in the next phase.

Create `docs/architecture.md` frontend section if not present, describing:

- Presentation: React components
- Service: `CardService`
- Repository: `HttpCardRepository`
- Data access: axios `http` client
- State/caching: TanStack Query + optimistic mutations
- Shared LexoRank utility with backend

# Real-time (WebSocket + Redis Pub/Sub)

## Goals
- WebSocket endpoint with JWT handshake auth
- Per-board rooms (isolation)
- Redis Pub/Sub bridge for multi-worker broadcast
- Presence tracking (Redis set + TTL heartbeat)
- Broadcast card create/update/move/delete and comments
- Frontend SocketClient with reconnect + useBoardSocket
- Live updates with no manual refresh

## Design decisions

### Why a Redis Pub/Sub bridge?
A single process can broadcast in memory, but with multiple Uvicorn
workers or replicas, a socket connected to worker A must receive
events produced on worker B. Each worker publishes domain events to a
Redis channel and subscribes to it, then fans out to its own local
sockets.

### Room model
One logical room per board: `board:{board_id}`. A connection joins
exactly one board room after authenticating and passing an RBAC check
(the user must be able to read the board).

### Presence
Redis set `presence:board:{board_id}` holds user ids, each refreshed
with a TTL heartbeat. On disconnect or TTL expiry the user is removed.
Presence changes are themselves broadcast.

### Auth handshake
The client sends the access token as a query parameter or first
message. We validate it exactly like HTTP auth, reject with a close
code on failure. No token, no room.

### Event envelope
    {
      "type": "card.moved",
      "board_id": "...",
      "payload": { ... },
      "actor_id": "...",
      "ts": "ISO-8601"
    }

### publish-after-commit

Refactored realtime event emission from "publish inside the service"
to "queue in the service, publish in the route after commit".

- Services accumulate RealtimeEvent objects and expose collect_events().
- Routes publish collect_events() only after session.commit() succeeds.
- Services no longer depend on RedisEventBridge, which makes event
  emission unit-testable without Redis.

Rationale: a failed commit must not broadcast a change that rolled
back. The transaction owner (the route) is the correct place to
publish.

## Open questions
- Should mutation HTTP endpoints publish events, or should a service
  layer publish? Decision: publish in the service layer so both HTTP
  and future sources stay consistent.

