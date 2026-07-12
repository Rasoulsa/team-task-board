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

## Next

Kanban UI with @dnd-kit, optimistic reorder using the shared
LexoRank util, CardModal, and TanStack Query caching.