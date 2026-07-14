# Team Task Board

A real-time Trello-style task-management platform for organizations, projects, boards, and collaborative Kanban workflows.

**Stack:** FastAPI · PostgreSQL · Redis · Celery · WebSocket · React · Vite · TypeScript · Docker

## Current implementation

The project currently provides a complete foundation for organization-based task management:

- JWT authentication with refresh-token rotation
- Password-reset token foundation
- Redis-backed authentication rate limiting
- Organization-scoped RBAC
- Projects, boards, and configurable board columns
- Cards, ordering, comments, mentions, checklists, labels, and assignees
- Card soft delete and restore
- Board activity records
- React authentication flow and authenticated application shell
- Projects and boards frontend views

Kanban drag-and-drop, real-time UI updates, notifications, reporting, and CI/CD are planned next.

---

## Quick start

### Docker

```bash
cp .env.example .env
docker compose up --build
```

After the services are ready:

- API documentation: http://localhost:8010/docs
- API health check: http://localhost:8010/health
- Frontend: http://localhost:5174
> Port values may differ if you customized them in .env or docker-compose.yml.

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

**Backend**
```text
backend/
├── app/
│   ├── api/            # FastAPI routers and dependencies
│   ├── core/           # Settings, security, logging, exceptions
│   ├── db/             # Database session and base configuration
│   ├── models/         # SQLAlchemy models
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

Refer to the interactive OpenAPI documentation for the exact request and response schemas available in the current backend version.

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
docker compose up -d db redis
Backend
bash
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

```awk
VITE_API_URL=http://localhost:8010/api/v1
```

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
```

>`make down` runs `docker compose down -v`, which removes Docker volumes and therefore >deletes local database data.

## Roadmap progress
[x] Repository, tooling, and DevOps foundation
[x] Backend authentication and frontend authentication shell
[x] RBAC, projects, boards, columns, and application shell
[x] Cards, ordering, comments, mentions, and activity logging backend
[x] Kanban board UI and drag-and-drop interaction
[ ] Real-time updates with WebSockets
[ ] Notifications and Celery background tasks
[ ] Reporting, caching, and activity feed UI
[ ] Production Docker, Nginx, and observability
[ ] CI/CD, end-to-end testing, documentation, and final polish

## Development notes
- Never commit .env files, access tokens, database passwords, or production secrets.
- Use strong values for JWT/HMAC secrets. SHA-256 signing keys should be at least 32 bytes.
- Run Alembic migrations before starting a backend against a new database.
- Keep the backend and frontend LexoRank implementations aligned.
- Treat the backend as the authorization and data-validation source of truth.

---

## Documentation

Detailed technical documentation is maintained in the [`docs/`](./docs) directory.

Recommended documentation structure:

```text
docs/
├── architecture.md       # Application architecture and design decisions
├── api.md                # API conventions and endpoint notes
├── database.md           # Database entities and migration notes
├── security.md           # Authentication, authorization, and security decisions
├── testing.md            # Test strategy and local test setup
└── journal.md            # Development progress and implementation journal
```

---

## License