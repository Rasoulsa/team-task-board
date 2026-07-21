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

# Reporting, Caching & Activity Feed

## Goals
- Board-level activity feed with cursor pagination
- Board stats aggregation endpoint (cards per column, done vs open, avg age)
- Redis-backed board cache with write-through invalidation on mutations
- Frontend reporting slice: stats dashboard (Recharts) + activity feed UI

## What shipped

### Backend
- `BoardColumn.is_done_column` — explicit flag to mark a column as "done state"
  instead of inferring from column name. Used by stats aggregation.
- `ActivityLog.actor` relationship added for author display in feed.
- Cursor pagination utility (`app/core/pagination.py`) — generic, reused by
  activity feed; unit tested independently (`tests/unit/test_pagination.py`).
- `GET /api/v1/boards/{board_id}/activity` — now returns
  `{ items: [...], next_cursor: str | null }` instead of a flat list.
  **Breaking change** for any existing consumer of this endpoint (frontend
  updated in same PR; test updated accordingly).
- `GET /api/v1/boards/{board_id}/stats` — single-query aggregation via
  SQLAlchemy `case()`/`func.count()` grouped by column, avoiding N+1 queries.
- `app/core/board_cache.py` — Redis cache for board detail payload
  (list of columns + cards), invalidated on every mutating route
  (card create/update/move/delete/restore, label/assignee changes,
  column CRUD, board update).
- Two migrations:
  - `a23966086a1c` — reporting & caching indexes (composite index on
    `activity_logs(board_id, created_at, id)` for cursor pagination)
  - `872aaa41e10e` — adds `is_done_column` to `board_column`

### Frontend
- `frontend/src/features/reporting/` — new feature slice:
  - `application/StatsService.ts`
  - `pages/StatsDashboard.tsx` (Recharts bar/pie charts)
  - `components/ActivityFeed.tsx` (paginated, "load more" cursor-based)
- `BoardPage.tsx` — added tab navigation (Board / Stats / Activity),
  each tab conditionally mounts its own component to avoid unnecessary
  polling/rendering cost when not visible.

## Issues hit & resolved
1. **Redis connection refused in CI** (`localhost:6380`) — Celery broker/result
   backend and Redis health checks needed to be wired correctly in
   docker-compose for the test environment; resolved by aligning `REDIS_URL`,
   `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` in `.env` with the mapped
   port (6380→6379) and adding explicit `depends_on: condition: service_healthy`.
2. **Duplicate index creation** — index for activity cursor pagination was
   already created in an earlier migration (`a23966086a1c`); confirmed via
   `alembic history` that the migration chain was linear and the index wasn't
   duplicated in `872aaa41e10e`.
3. **`app/main.py` session factory** — startup was using a raw `sessionmaker`
   instead of the shared `AsyncSessionLocal`; fixed to avoid divergent
   session configuration between app startup and request-scoped dependency.
4. **Activity feed test breakage** — `test_comment_with_mention_records_activity`
   asserted against the old flat-list response shape; updated to read
   `response.json()["items"]` after the cursor pagination change.

## Follow-ups (Day 9 candidates)
- Frontend bundle is single-chunk (~787kB / 236kB gzip) after adding Recharts.
  Consider lazy-loading `BoardPage`/reporting slice via `React.lazy` +
  `Suspense` to split the vendor chunk.
- Confirm frontend `package.json` `"test"` script uses `vitest run` (not bare
  `vitest`, which defaults to watch mode) for CI non-interactive runs.

## Test results
- Backend: 70 passed
- Frontend: 44 passed (14 files)
- `ruff check` / `ruff format` / `mypy`: clean
- Frontend `lint` / `build`: clean