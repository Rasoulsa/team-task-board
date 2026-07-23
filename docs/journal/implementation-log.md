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

  ## Notifications & Celery

- Added Celery app, worker, and Beat; Redis broker/result backend.
- Added `notifications` table + migration; NotificationRepository/Service.
- Added notify_card_assigned / notify_card_mentioned / notify_due_date
  tasks with retry (backoff + jitter) and email via SMTP (MailHog locally).
- Beat task scan_due_cards notifies assignees of cards due within
  DUE_REMINDER_HOURS.
- Added per-user WS channel + /ws/notifications for live bell updates,
  reusing the Day 6 SocketClient and event bridge.
- Frontend: NotificationBell (live unread badge), NotificationPanel,
  notification hooks + repository, useNotificationSocket.
- Tests: eager-mode task creation test (mock email + publish), unread-count
  endpoint test, NotificationBell render test.
- Compose: added celery-worker, celery-beat, mailhog services.

## Production Docker, Nginx & Observability

**Branch:** `feat/docker-nginx-observability`

### Goal
Bring the whole system up with one command behind Nginx, with multi-stage
non-root images, healthchecks, worker scaling, and an optional Prometheus +
Grafana observability profile.

### What was built
- Renamed the existing dev compose to `docker-compose.dev.yml`; added a new
  production-like `docker-compose.yml` where only Nginx (`8080`) is published.
- Backend: converted the Dockerfile to a true multi-stage build (builder +
  slim non-root runtime), added `/metrics` via
  `prometheus-fastapi-instrumentator`, added `backend/README.md` for the
  setuptools build, and run `alembic upgrade head` before serving.
- Frontend: multi-stage image serving the SPA on `8080` and proxying `/api`,
  `/api/v1/ws`, `/health`, `/docs`, and `/openapi.json` to the backend; built
  with relative Vite URLs for same-origin operation.
- Added `docker/prometheus/prometheus.yml` and Grafana datasource + dashboard
  provisioning under `docker/grafana/`.

### Issues hit and resolved
1. **`JWT_SECRET_KEY` blank warning** — `.env` lacked `SECRET_KEY` /
   `JWT_SECRET_KEY`; added them plus `CORS_ORIGINS` and Grafana credentials.
2. **Celery services reported `unhealthy`** — they inherited the backend
   image's HTTP `/health` healthcheck, which Celery cannot answer. Fixed with
   `healthcheck: disable: true` on `celery-worker` and `celery-beat`.
3. **Frontend crash-looping (`/run/nginx.pid` permission denied)** — an early
   attempt to run Nginx fully rootless (`USER nginx` + rewriting the pid path)
   broke Nginx's default pid handling. Resolved by using the stock
   `nginx:1.27-alpine` (master as root, workers drop to the `nginx` user),
   which is the standard and reliable pattern. Full rootless Nginx noted as
   future hardening.
4. **Healthcheck flapping** — BusyBox `wget` in the Nginx alpine image behaved
   inconsistently; installed `curl` and used it for the frontend healthcheck.
5. **`/api/v1/docs` returned 404** — the backend mounts Swagger at `/docs` and
   the schema at `/openapi.json` (app root), not under `/api/v1`. Added
   explicit `/docs` and `/openapi.json` proxy blocks to `nginx.conf`.

### Verification
- `docker compose up --build` → all services healthy; SPA served at
  `http://localhost:8080`.
- API reachable through the proxy; `/openapi.json` and `/docs` served through
  Nginx; live board updates confirmed between two browser sessions over the
  proxied WebSocket.
- `docker compose up -d --scale celery-worker=3` → three workers.
- `docker compose --profile observability up -d` → Prometheus target `UP`,
  Grafana "Backend Overview" dashboard provisioned.

### Notes / follow-ups
- Consider a real Celery liveness probe (`inspect ping`) instead of disabling.
- Consider a fully rootless Nginx image if required by deployment policy.
- Mailhog is internal-only in the production stack; expose `8025` if a demo
  needs the UI.

## CI/CD, E2E, Docs & Release

**Branch:** `feat/cicd-e2e-docs`

### Goal
Complete the delivery pipeline: full GitHub Actions (lint → type-check → tests →
build → E2E → GHCR publish), Playwright end-to-end coverage of the core
real-time flow, Swagger polish with OpenAPI export, coverage on both stacks,
final documentation, and the `v1.0.0` release.

### What was built
- **CI/CD** (`.github/workflows/ci.yml`): parallel backend quality/tests
  (Postgres + Redis service containers, migrations, pytest+coverage), frontend
  lint/test/build, a full-stack Playwright E2E job against the Compose stack,
  and a GHCR publish job gated to `main` and version tags with semver/sha/branch
  image tags.
- **E2E** (`e2e/`): standalone Playwright package; scenario covers register →
  project → board → card → cross-session drag with live WebSocket update
  through Nginx.
- **Swagger polish**: enriched app metadata, ordered OpenAPI tags, contact/
  license, and a `scripts/export_openapi.py` exporter writing
  `docs/api/openapi.json`.
- **Coverage**: backend coverage config in `pyproject.toml`; frontend v8
  coverage in the Vitest config; both uploaded as CI artifacts.
- **Docs**: new `docs/architecture/cicd-e2e.md`; README updated with pipeline,
  running instructions, design-decision summaries, and screenshots.

### Issues hit and resolved
<!-- fill in the real ones as you run it, e.g.: -->
- (Record: GHCR lowercase image name, dnd-kit drag needing stepped mouse moves,
  E2E selector alignment via data-testid, wait-for-/health loop tuning.)

### Verification
- CI green on the PR (all jobs).
- Playwright report shows the real-time scenario passing.
- GHCR shows `backend` and `frontend` images tagged `1.0.0` after the tag push.

### Release
- Merged to `main`, tagged `v1.0.0`, images published to GHCR.