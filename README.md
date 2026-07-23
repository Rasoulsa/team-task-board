# Team Task Board

A real-time Trello-style task-management platform for organizations, projects, boards, and collaborative Kanban workflows.

**Stack:** FastAPI · PostgreSQL · Redis · Celery · WebSocket · React · Vite · TypeScript · Docker

## Current implementation

The project currently provides a complete foundation for organization-based task management, a fully interactive Kanban board, live real-time updates, background notifications, and board-level reporting:

- JWT authentication with refresh-token rotation
- Password-reset token foundation
- Redis-backed authentication rate limiting
- Organization-scoped RBAC
- Projects, boards, and configurable board columns
- Cards, ordering, comments, mentions, checklists, labels, and assignees
- Card soft delete and restore
- Board activity log, now cursor-paginated
- Board stats dashboard (cards per column, done vs. open, overdue)
- Redis-backed board cache with write-through invalidation
- Assignment, mention, and due-date notifications, delivered in-app and by email via Celery
- React authentication flow and authenticated application shell
- Projects and boards frontend views
- Kanban board with drag-and-drop columns and cards
- Real-time board updates over WebSocket, with online presence tracking
- Live notification bell with unread count over WebSocket

---

## Quick start

### Docker

```bash
cp .env.example .env
docker compose up --build
```

Everything is served behind Nginx on a single port:
- App (SPA): http://localhost:8080
- API through the proxy: http://localhost:8080/api/v1
- API docs: http://localhost:8080/docs
- Health: http://localhost:8080/health

With the observability profile:

```bash
docker compose --profile observability up -d
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (default `admin`/`admin`)

Scale the Celery workers:

```bash
docker compose up -d --scale celery-worker=3
```

### Docker (development, hot reload + exposed ports)

```bash
docker compose -f docker-compose.dev.yml up --build
```

- API documentation: http://localhost:8010/docs
- API health check: http://localhost:8010/health
- Frontend: http://localhost:5174

> Port values may differ if you customized them in `.env` or the compose files.

**Stop containers**
```bash
docker compose down
```

To also remove named volumes, including local database data:
```bash
docker compose down -v
```

---

## Architecture
The application follows a layered architecture:

```text
Presentation / API
        ↓
Service layer
        ↓
Repository layer
        ↓
Data layer (PostgreSQL, Redis)
```

Real-time updates run alongside this flow: services return domain events,
routers publish them to Redis Pub/Sub after a successful commit, and a
per-process WebSocket ConnectionManager broadcasts them to connected clients
on the relevant board. See
[docs/architecture/realtime-websocket.md](docs/architecture/realtime-websocket.md)
for details.

Notifications and scheduled reminders run through Celery: services enqueue
a task after a successful commit, a worker delivers the in-app notification
and/or email, and a beat schedule periodically checks for upcoming due dates.
See [docs/architecture/notifications-celery.md](docs/architecture/notifications-celery.md).

Board reads are served from a Redis cache and invalidated on every mutating
route so cached data never outlives its underlying change. See
[docs/architecture/reporting-caching.md](docs/architecture/reporting-caching.md).

**Backend**
```text
backend/
├── app/
│   ├── api/            # FastAPI routers and dependencies (incl. WebSocket routes)
│   ├── core/           # Settings, security, logging, exceptions
│   ├── db/             # Database session and base configuration
│   ├── models/         # SQLAlchemy models
│   ├── realtime/        # ConnectionManager, Redis EventBridge, presence tracker
│   ├── repositories/   # Database query and persistence abstractions
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Business rules and application workflows
│   └── utils/          # Shared backend utilities, including LexoRank
├── alembic/            # Database migrations
└── tests/              # Unit and integration tests
```

**Frontend**
```text
frontend/
└── src/
    ├── app/            # Routing and application composition
    ├── core/           # HTTP client, configuration, shared utilities
    ├── features/       # Feature-oriented UI, services, repositories, state
    │   └── realtime/   # SocketClient, useBoardSocket
    └── shared/         # Shared UI components and common types
```

The frontend also uses separation of concerns through repositories, services, state stores, and React components.

## Features

### Authentication and security
- User registration with organization creation
- JWT access tokens
- Refresh-token rotation
- Redis-backed refresh-token session storage
- Refresh-token revocation and blacklist support
- Password-reset token workflow foundation
- Authentication rate limiting through Redis
- Secure password hashing
- Organization-scoped authorization

### Organization RBAC
Supported organization roles:
- **Owner**
- **Admin**
- **Member**
- **Viewer**

Permissions are enforced by backend dependencies and service-layer authorization checks.

### Projects and boards
- Organization project CRUD
- Project board CRUD
- Board column CRUD
- Configurable column ordering
- Organization invitation management foundation
- Board and project access based on organization membership

### Task management
- Cards with title, description, priority, and due date
- Labels, assignees, and checklist items
- LexoRank ordering for cards and columns
- Reorder cards without renumbering every sibling
- Move cards within a column
- Move cards across board columns
- Comments with @mention parsing
- Soft delete and restore cards
- Board activity log preserved across card deletion and restoration

### Notifications
- In-app notifications for card assignment, @mentions in comments, and upcoming due dates
- Live unread-count bell over a dedicated WebSocket channel (/api/v1/ws/notifications)
- Email delivery via Celery worker, using Mailhog for local development
- Scheduled due-date reminder sweep via Celery beat
- Mark-as-read and mark-all-as-read endpoints

### Reporting and caching
- Board stats endpoint: cards per column, done vs. open counts, and overdue count, computed with a single aggregated query
- Board activity feed, cursor-paginated to stay performant as history grows
- Redis-backed cache for board detail reads, invalidated on every mutating route (card create/update/move/delete/restore, label/assignee changes, column CRUD, board update) so stale data is never served
- Frontend stats dashboard (Recharts) and activity feed UI, presented as tabs on the board page

### Real-time updates
- WebSocket endpoint per board (/api/v1/ws/boards/{board_id}) with JWT auth handshake
- Redis Pub/Sub bridge so events broadcast correctly across multiple backend replicas
- Live broadcast of card creation, update, move, delete, restore, and new comments to every connected board member
- Redis-backed presence tracking (TTL heartbeat) per board
- Self-originated events are filtered client-side to avoid redundant refetches after an optimistic update
- No manual page refresh required to see changes made by other members

### Deployment and observability
- Multi-stage backend and frontend images; backend runs as a non-root user
- Container healthchecks on `db`, `redis`, `backend`, and `frontend`
- Single production-like Compose stack served entirely behind Nginx on port `8080`
- Nginx serves the React build and proxies `/api`, `/api/v1/ws`, `/health`, and `/docs`
- Frontend built with relative API/WS URLs for same-origin operation (no CORS in production path)
- Database migrations run automatically on backend startup
- Prometheus metrics at `/metrics` with an optional Prometheus + Grafana observability profile
- Horizontal Celery worker scaling via `--scale celery-worker=3`

See [docs/architecture/deployment-observability.md](docs/architecture/deployment-observability.md).

### Frontend
- Authentication pages for registration and login
- Persisted authenticated session state
- Protected application routes
- Authenticated application shell
- Sidebar and top navigation
- Organization-aware projects page
- Board listing and board-column UI
- API client with token handling
- Repository and service abstractions for frontend API access
- Kanban board with draggable columns and cards (@dnd-kit)
- Optimistic card reordering using client-side LexoRank
- Card modal with title, description, priority, due date, checklist, labels, assignees
- TanStack Query caching with optimistic updates and invalidation
- CardRepository and CardService
- SocketClient and useBoardSocket hook for live board updates
- NotificationBell with live unread count and mark-as-read actions
- Board page stats and activity tabs backed by the reporting API

---

## RBAC policy
```text
| Resource action | Minimum role |
|---|---|
| Read organization projects | Viewer |
| Create or update projects | Member |
| Delete projects | Admin |
| Read boards and columns | Viewer |
| Create or update boards | Member |
| Delete boards | Admin |
| Create, update, or delete columns | Member |
| Manage invitations | Admin |
| Create, update, move, restore, or delete cards | Member |
| Read cards, comments, labels, and activity | Viewer |
| Create comments | Member |
| Read board stats | Viewer |
```
The backend remains the source of truth for all authorization decisions.

---

## Shared utilities

### LexoRank ordering

The LexoRank ordering algorithm is intentionally implemented on both stacks.

- **Backend source of truth:** `backend/app/utils/lexorank.py`
- **Frontend optimistic copy:** `frontend/src/core/lexorank/lexorank.ts`

LexoRank allows cards and columns to be inserted or moved between neighboring items without reindexing every item in the list.

Any algorithm changes must be applied consistently to both implementations to ensure frontend optimistic updates generate ranks compatible with backend validation and persistence.

---

## API

The API is versioned under:

```text
/api/v1
```

Interactive API documentation is available when the backend is running:
```text
http://localhost:8010/docs
```

### Authentication
```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
```

### Organizations and invitations
```text
GET    /api/v1/organizations
GET    /api/v1/organizations/{organization_id}/invitations
POST   /api/v1/organizations/{organization_id}/invitations
POST   /api/v1/invitations/{invitation_id}/revoke
```

### Projects
```text
GET    /api/v1/projects?organization_id={organization_id}
POST   /api/v1/projects
GET    /api/v1/projects/{project_id}
PATCH  /api/v1/projects/{project_id}
DELETE /api/v1/projects/{project_id}
```

### Boards and columns
```text
GET    /api/v1/projects/{project_id}/boards
POST   /api/v1/projects/{project_id}/boards

GET    /api/v1/boards/{board_id}
PATCH  /api/v1/boards/{board_id}
DELETE /api/v1/boards/{board_id}

GET    /api/v1/boards/{board_id}/columns
POST   /api/v1/boards/{board_id}/columns
PATCH  /api/v1/columns/{column_id}
DELETE /api/v1/columns/{column_id}
```

### Cards, comments, and activity

The card-management API supports card creation, update, movement, soft deletion, restoration, labels, assignees, checklist items, comments, mentions, and board activity retrieval.
```text
GET    /api/v1/boards/{board_id}/activity?cursor={cursor}&limit={limit}
```

Refer to the interactive OpenAPI documentation for the exact request and response schemas available in the current backend version.

### Reporting
```text
GET    /api/v1/boards/{board_id}/stats
```
Returns aggregated card counts by column, done vs. open totals, and overdue count for a board.

### Notifications
```text
GET    /api/v1/notifications
GET    /api/v1/notifications/unread-count
POST   /api/v1/notifications/{notification_id}/read
POST   /api/v1/notifications/read-all
GET    /api/v1/ws/notifications
```

### Real-time (WebSocket)

```text
GET    /api/v1/ws/boards/{board_id}
GET    /api/v1/ws/notifications
```

See [docs/api/websocket.md](docs/api/websocket.md) for the connection handshake, message envelope, and event type reference.

---

## Running locally

### Prerequisites
- Python 3.13+
- uv
- Node.js 20+
- npm
- Docker and Docker Compose
- PostgreSQL and Redis, or the provided Docker services

### Start infrastructure services

From the repository root:

```bash
docker compose up -d db redis mailhog
```

### Backend
```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8010
```

The local backend is then available at:

```text
http://localhost:8010
http://localhost:8010/docs
```

### Celery worker, beat, and Mailhog
Notifications and scheduled due-date reminders require a running worker and
beat scheduler. In separate terminals from `backend/`:

```bash
uv run celery -A app.worker.celery_app.celery_app worker --loglevel=info
uv run celery -A app.worker.celery_app.celery_app beat --loglevel=info
```

Sent emails during local development can be viewed in Mailhog:

```text
http://localhost:8025
```

### Frontend
In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5174
```

Ensure the frontend API URL environment variable points to your local backend, for example:

```ini
VITE_API_URL=http://localhost:8010/api/v1
VITE_WS_URL=ws://localhost:8010/api/v1/ws
```

---

## Environment variables
In addition to database and JWT settings, the following are required for
notifications and background tasks:

```ini
CELERY_BROKER_URL=redis://localhost:6380/0
CELERY_RESULT_BACKEND=redis://localhost:6380/0
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_FROM=noreply@teamtaskboard.local
DUE_REMINDER_HOURS=24
```

`SMTP_HOST`/`SMTP_PORT` point at Mailhog in local development; configure a
real SMTP provider for production.

---

## Testing and quality checks

### Backend

Run from `backend/`:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy app
uv run pytest -v
```

Run tests with coverage:

```bash
uv run pytest -v --cov=app
```

Real-time-specific tests live under `backend/tests/realtime/` and cover
WebSocket connect/accept behavior, auth handshake rejection, and event
broadcast through the Redis Pub/Sub bridge.

Integration tests for background tasks (notifications, due-date reminders)
and for the Redis board cache require a running Redis instance; see
“Test environment notes” below.

### Frontend

Run from `frontend/`:

```bash
npm run lint
npm run test -- --run
npm run build
```

### Test environment notes

Integration tests use PostgreSQL and Redis. Use a separate database and Redis database for test execution where possible.

For example:

```ini
ENV=testing
REDIS_URL=redis://localhost:6380/1
CELERY_BROKER_URL=redis://localhost:6380/1
CELERY_RESULT_BACKEND=redis://localhost:6380/1
```

This prevents test-created data, refresh tokens, and rate-limit counters from affecting local development sessions.

Authentication rate-limit keys are Redis-backed and should be isolated or cleared between integration tests. Avoid using `FLUSHDB` against a Redis database shared with the development application.

---

## Makefile commands

The repository `Makefile` provides common Docker and backend commands:

```makefile
.PHONY: up down build logs test lint fmt migrate

up:        ; docker compose up --build
down:      ; docker compose down -v
build:     ; docker compose build
logs:      ; docker compose logs -f
migrate:   ; docker compose exec backend alembic upgrade head

lint:      ; cd backend && ruff check . && mypy app
fmt:       ; cd backend && ruff check --fix . && black .
test:      ; cd backend && pytest -v --cov=app

fe-lint:   ; cd frontend && npm run lint
fe-test:   ; cd frontend && npm run test

dev:       ; docker compose -f docker-compose.dev.yml up --build
```

Examples:

```bash
make up
make logs
make migrate
make test
make lint
make fe-lint
make fe-test
make down
make dev
```

>`make down` runs `docker compose down -v`, which removes Docker volumes and therefore >deletes local database data.

## Roadmap progress
[x] Repository, tooling, and DevOps foundation
[x] Backend authentication and frontend authentication shell
[x] RBAC, projects, boards, columns, and application shell
[x] Cards, ordering, comments, mentions, and activity logging backend
[x] Kanban board UI and drag-and-drop interaction
[x] Real-time updates with WebSockets
[x] Notifications and Celery background tasks
[x] Reporting, caching, and activity feed UI
[x] Production Docker, Nginx, and observability
[ ] CI/CD, end-to-end testing, documentation, and final polish


## Development notes

- Never commit .env files, access tokens, database passwords, or production secrets.
- Use strong values for JWT/HMAC secrets. SHA-256 signing keys should be at least 32 bytes.
- Run Alembic migrations before starting a backend against a new database.
- Keep the backend and frontend LexoRank implementations aligned.
- Treat the backend as the authorization and data-validation source of truth.
- Card mutations must commit to the database before their corresponding real-time event is published, so remote clients never see an event for a change that was rolled back.
- Board cache invalidation must happen from the same code path as every mutating route; a new mutation that forgets to call `invalidate_board()` will silently serve stale board reads.


---

## Documentation

Detailed technical documentation is maintained in the [`docs/`](./docs) directory.

Recommended documentation structure:

```text
docs/
├── api/
│   ├── cards.md                          # Card, comment, label, checklist API notes
│   ├── endpoints.md                      # Full REST endpoint reference
│   └── websocket.md                      # WebSocket connection, auth, and event contract
├── architecture/
│   ├── backend-rbac-projects-boards.md
│   ├── cards-ordering-comments.md
│   ├── deployment-observability.md       # Docker, Nginx, Prometheus/Grafana, scaling
│   ├── frontend-app-shell.md
│   ├── kanban-ui-dnd.md
│   ├── notifications-celery.md
│   ├── realtime-websocket.md
│   └── reporting-caching.md                 # Kanban board, drag-and-drop, optimistic LexoRank reorder
│   └── realtime-websocket.md             # ConnectionManager, Redis Pub/Sub bridge, presence
└── journal/
    └── implementation-log.md             # Day-by-day implementation journal
```

---

## License

see the [`LICENSE`](./LICENSE)