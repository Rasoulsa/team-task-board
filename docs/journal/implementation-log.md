# Implementation Log

## Title

RBAC, Projects/Boards Backend, and Frontend App Shell

## Summary

This phase expands the authenticated product foundation into an organization-scoped task management structure.

## Backend work completed

- Added RBAC helper module
- Added project model, schema, repository, service, and API routes
- Added board model, schema, repository, service, and API routes
- Added board column model, schema, repository, service, and API routes
- Added organization listing endpoint for current user
- Added basic invitation list/create/revoke endpoints
- Added Alembic migration for projects, boards, and columns
- Added RBAC unit tests

## Frontend work completed

- Added authenticated app shell
- Added sidebar navigation
- Added topbar with notification bell placeholder
- Added project repository/service/page
- Added board repository/service/page
- Added board columns preview and create form
- Added frontend unit tests for project and board services

## Design decisions

### Integer column ordering for now

Columns use simple integer positions in this phase. Card ordering will use LexoRank in the next backend card phase.

### RBAC in service layer

Route handlers remain thin. Permission checks are executed in service methods close to business logic.

### Frontend repository/service pattern

The frontend continues using repository interfaces and service classes to keep UI pages independent from HTTP implementation details.

## Next phase

The next phase will add cards, card ordering, comments, mentions, soft delete, restore, and activity log foundations.


# Cards, Ordering, Comments

Date: 2026-07-12
Branch: feat/cards-ordering-comments

## Goal

Implement the task domain: cards with labels/priority/due date/checklist/
assignees, LexoRank ordering, comments with @mentions, soft delete/restore,
and a preserved activity log.

## What was built

- New models: cards, card_labels, card_assignees, checklist_items,
  comments, comment_mentions, activity_logs.
- Shared LexoRank algorithm on backend and frontend.
- Repository + service layers for cards, comments, activity.
- REST endpoints under /api/v1 with RBAC enforcement.
- Alembic migration for all new tables and indexes.
- Unit tests for LexoRank edge cases.
- Integration tests for card CRUD, ordering, soft delete/restore,
  move between columns, and comment mentions producing activity.

## Design decisions

- LexoRank over integer positions to avoid sibling renumbering and to
  support optimistic drag & drop later.
- Soft delete instead of hard delete so activity history is preserved.
- Activity log keyed by board to power the feed and future reporting.
- Mentions matched by email local-part for now; can move to a proper
  username field later.

## Testing notes

- `pytest tests/unit/test_lexorank.py` covers ordering edge cases.
- Integration tests use the existing testcontainers fixtures.
- Frontend `lexorank.test.ts` mirrors backend behavior.

## Kanban UI & drag-and-drop (backfilled)

- Built `KanbanBoard`, `ColumnLane`, and `CardItem` using `@dnd-kit/core` and
  `@dnd-kit/sortable`.
- Implemented optimistic reordering: rank computed client-side via the
  shared LexoRank implementation, cache updated immediately via TanStack
  Query, then persisted through `useMoveCard`, with rollback on failure.
- Added `CardModal` covering title, description, priority, due date,
  checklist, labels, and assignees.
- Added `CardRepository`/`CardService` and card mutation hooks
  (`useCreateCard`, `useMoveCard`, `useUpdateCard`, `useDeleteCard`,
  `useRestoreCard`, label/assignee/checklist hooks), all reading/writing a
  single board-scoped query cache entry.
- Added response normalization in `CardRepository` (e.g.
  `checklist_items` → `checklist`) so components use one consistent `Card`
  shape regardless of backend field naming.

## Real-time updates

- Added `ConnectionManager` for per-board WebSocket connection registries.
- Added Redis Pub/Sub `EventBridge` so events broadcast correctly across
  multiple backend replicas, not just the process holding the connection.
- Card service mutations (create, update, move, delete, restore) and comment
  creation now return domain events; the router publishes them after the DB
  transaction commits successfully.
- Added WebSocket auth handshake: token validated via query param before
  accepting the connection; board membership enforced before accept.
- Added Redis-set + TTL-based presence tracking per board.
- Frontend: added `SocketClient` (reconnect-aware WebSocket wrapper) and
  `useBoardSocket` hook. Board view now updates live for card moves, edits,
  deletes, restores, and new comments without a manual refresh.
- Self-originated events are filtered out on the frontend using `actor_id`
  to avoid redundant refetches / flicker after an optimistic update.
- Verified with a two-session manual test: mutation in session B reflects in
  session A live; mutation in session A does not trigger a redundant
  refetch in session A itself.