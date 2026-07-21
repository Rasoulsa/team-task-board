# Reporting, Caching, and Activity Feed

This document covers the three features added on top of the existing board
domain: board statistics reporting, the Redis-backed board read cache, and
cursor-paginated board activity.

---

## 1. Board statistics

### Goal

Give a board a lightweight "at a glance" view: how many cards per column,
how many are done vs. still open, and how many are overdue — without the
frontend having to fetch every card and compute this client-side.

### Endpoint

```text
GET /api/v1/boards/{board_id}/stats
```

Minimum role: Viewer (same as reading the board itself).

### Response shape

```json
{
  "board_id": "…",
  "total_cards": 42,
  "done_cards": 17,
  "open_cards": 25,
  "overdue_cards": 3,
  "by_column": [
    { "column_id": "…", "column_name": "To Do", "card_count": 12 },
    { "column_id": "…", "column_name": "In Progress", "card_count": 13 },
    { "column_id": "…", "column_name": "Done", "card_count": 17 }
  ]
}
```

### “Done” is determined by column, not name

Cards don’t have their own status field. A card is considered **done** if it
currently sits in a column where `BoardColumn.is_done_column = True`.

This was a deliberate choice over matching on column name (e.g. `"Done"`),
because:

- Column names are user-editable and not guaranteed to be `"Done"` in any language or casing.
- A board can reasonably have more than one terminal column (e.g. `"Done"` and `"Won't do"`), and both should count as closed.
- It keeps the reporting logic decoupled from display text.

`is_done_column` is set at column-creation/update time via the board columns
API and defaults to `False`. Only one aggregation query is needed:

```sql
SELECT c.column_id, count(*) AS card_count, bc.is_done_column
FROM cards c
JOIN board_columns bc ON bc.id = c.column_id
WHERE c.board_id = :board_id AND c.deleted_at IS NULL
GROUP BY c.column_id, bc.is_done_column;
```
`overdue_cards` is computed from `due_date < now()` for cards not in a
done column — a card in a done column past its due date is not counted as
overdue.

### Implementation location
- `app/services/stats_service.py` — aggregation query and response assembly
- `app/api/v1/routes/stats.py` — route handler, permission check
- `app/schemas/stats.py` — `BoardStatsResponse`, `ColumnStats`

### Caching
Stats reads go through the same board cache described below (§2), keyed
separately from the board detail payload, and are invalidated by the same
`invalidate_board(board_id)` call after any card mutation.

---

## 2. Board read cache

### Goal

Reduce repeated database load for board detail reads (columns + cards +
labels + assignees), which is the single most frequently fetched payload in
the app (polled implicitly by every board page load, and re-fetched after
every mutation before real-time events are relied upon).

### Cache keys
```text
board:{board_id}:detail   → serialized board detail payload
board:{board_id}:stats    → serialized stats payload
```

### TTL
A short TTL (e.g. 60s) is used as a safety net in case an invalidation call
is ever missed, so cache staleness is bounded even in the worst case.

### Redis client access pattern
The Redis client is stored on `app.state.redis`, set up once at application
startup (see `app/main.py` lifespan handler), and exposed to route handlers
through a FastAPI dependency rather than read directly from `app.state`:

```python
# app/core/deps.py (or similar)
async def get_redis(request: Request) -> Redis:
    return request.app.state.redis
```
Routes and services depend on `get_redis` (or receive the client injected by
a caching decorator/helper) rather than importing `app.state` directly, to
keep them testable — tests can override the dependency with a fake/mocked
Redis client instead of relying on `app.state`.

### Invalidation strategy: write-through on every mutation
The cache is invalidated — not updated in place — on every route that
changes board-affecting state. This includes:

- Card create, update, move, delete, restore
- Card label add/remove
- Card assignee add/remove
- Checklist item create/update/delete
- Column create, update, delete, reorder
- Board update (name, etc.)
Each of these routes calls a shared helper after a successful commit:

```python
await invalidate_board(redis, board_id)
```

which deletes both the `:detail` and `:stats` keys for that board.

**This is the single most important invariant of this feature:** any new
mutating route added to `cards.py`, `columns.py`, or `boards.py` in the
future must call `invalidate_board()` in its success path, or board
reads will silently serve stale data until the TTL expires. There’s no
automatic mechanism that enforces this — it’s a manual discipline enforced
by code review and the `test_board_cache_invalidation.py` integration test
suite covering the known mutation list above.

### Why invalidate instead of update-in-place
Update-in-place (patching the cached payload directly) was considered and
rejected for now:

- Every mutation would need to know how to patch the cached representation precisely (e.g. reordering by LexoRank, nested label objects), which duplicates serialization logic and is easy to get subtly wrong.
- Invalidation is simpler to reason about and verify: the next read is always a guaranteed-fresh read from the database.
- Board reads are frequent but individually cheap once cached; the cost of a cache miss recomputing the full board detail is acceptable relative to the complexity of correct partial updates.

This can be revisited if board detail payloads become large enough that
full recomputation on every mutation becomes a bottleneck.

---

## 3. Activity feed pagination

### Goal

The board activity log (`ActivityLog` model) grows unbounded over a board’s
lifetime. Returning the full history on every request doesn’t scale, so the
activity endpoint uses cursor-based pagination instead of offset-based
pagination.

### Endpoint
```text
GET /api/v1/boards/{board_id}/activity?cursor={cursor}&limit={limit}
```
### Response shape
```json
{
  "items": [
    {
      "id": "…",
      "action": "card_moved",
      "actor": { "id": "…", "name": "…" },
      "card_id": "…",
      "created_at": "…"
    }
  ],
  "next_cursor": "opaque-cursor-string-or-null"
}
```

### Why cursor-based instead of offset/limit
- Offset pagination (`?offset=200&limit=20`) degrades in correctness when new activity rows are inserted between page requests — a client can see duplicate or skipped rows if activity is written concurrently with reading, which is common on an active board.
- Cursor pagination anchors each page to the last-seen row (typically encoding `created_at` + `id` to break ties), so it stays stable regardless of concurrent writes.
- It also avoids the performance cliff of large `OFFSET` values in PostgreSQL, which has to scan and discard all preceding rows.

### Cursor encoding
The cursor is an opaque, base64-encoded representation of
(`created_at`, `id`) of the last item in the previous page. The repository
query filters on:

```sql
WHERE (created_at, id) < (:cursor_created_at, :cursor_id)
ORDER BY created_at DESC, id DESC
LIMIT :limit
```

`next_cursor` is `null` when fewer than `limit` rows are returned, signaling
the end of the feed.

Implementation location
- `app/repositories/activity.py` — cursor-filtered query
- `app/core/pagination.py` — cursor encode/decode helpers, shared with any future paginated endpoint
- `app/api/v1/routes/activity.py` — route handler

---

## 4. Frontend

### Stats dashboard

`frontend/src/features/reporting/` provides a `StatsService` /
`HttpStatsRepository` pair (following the same repository/service pattern as
`BoardService` / `HttpBoardRepository`) and a `StatsDashboard` component that
renders the column breakdown and done/open/overdue counts using
Recharts.

Recharts was chosen because it’s a thin, composable wrapper around SVG with
good TypeScript support and no separate CSS/theme system to integrate,
which fit the existing Tailwind-based styling with the least friction.

### Activity feed

The activity feed UI consumes the cursor-paginated endpoint via TanStack
Query’s `useInfiniteQuery`, using `next_cursor` as the `getNextPageParam`
value, and renders as an infinite-scroll (or “load more”) list on the board
page’s Activity tab.

### Board cache interaction from the frontend’s perspective

The frontend cache (TanStack Query) is separate from the backend Redis
cache and is invalidated independently, based on real-time WebSocket events
and optimistic mutation responses — the two caching layers don’t need to be
aware of each other. The Redis cache only affects how fast the backend
responds to a given request; it doesn’t change the frontend’s own
invalidation logic.

---

## 5. Testing

- `tests/integration/test_stats.py` — verifies stats aggregation correctness against seeded boards/columns/cards, including the `is_done_column` and overdue logic, using the `seed_board_with_column` and `authed_client` fixtures.
- `tests/integration/test_board_cache_invalidation.py` — verifies that after each mutating route (card create/update/move/delete/restore, label, assignee, column CRUD) a subsequent board-detail read reflects the change, i.e. that the cache was correctly invalidated rather than serving a stale cached copy.
- `tests/unit/test_pagination.py` — unit tests for cursor encode/decode round-tripping and boundary behavior (empty result set, exactly `limit` results, fewer than `limit` results).

---

## 6. Known limitations / future work

- The board cache uses a single Redis instance with no cache-tier fallback; if Redis is unavailable, reads currently fail rather than gracefully falling back to a direct database read.
- Stats are computed synchronously per request rather than pre-aggregated; this is fine at current expected board sizes but would need revisiting (e.g. a materialized view or scheduled aggregation) if boards grow into the tens of thousands of cards.
- Activity feed pagination direction is currently newest-first only; there’s no “jump to a specific point in time” capability.
