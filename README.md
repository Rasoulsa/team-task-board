# Team Task Board

Real-time Trello-style task management platform.

**Stack:** FastAPI · PostgreSQL · Redis · Celery · WebSocket · React (Vite + TS) · Docker

## Quick Start
```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000/docs
- Front: http://localhost:5173
- Health: http://localhost:8000/health


## Architecture

Layered (Presentation / Service / Repository / Data) + DI on both backend and frontend.

Development
See Makefile for common commands (make up, make test, make lint).

smali

### `Makefile`
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

## Current Implementation Status

| Phase | Status | Scope |
| ----- | ------ | ----- |
| Foundation | Complete | Monorepo, FastAPI, React, Docker baseline, tooling |
| Authentication | Complete | JWT auth, refresh rotation, password reset foundation, frontend auth shell |
| RBAC + Projects/Boards | Complete | Organization RBAC, projects, boards, columns, app shell |

## Features

### Backend

- Organization-scoped RBAC with Owner/Admin/Member/Viewer roles
- Projects CRUD
- Boards CRUD
- Board columns CRUD
- Basic invitation management
- Repository and service layers for business logic
- Alembic migration for project management tables

### Frontend

- Authenticated application shell
- Sidebar and topbar
- Notification bell placeholder
- Projects page
- Boards page
- Basic board columns UI
- ProjectRepository and ProjectService
- BoardRepository and BoardService

## RBAC Policy

```text
| Resource action | Minimum role |
| --------------- | ------------ |
| Read organization projects | Viewer |
| Create/update projects | Member |
| Delete projects | Admin |
| Read boards/columns | Viewer |
| Create/update boards | Member |
| Delete boards | Admin |
| Create/update/delete columns | Member |
| Manage invitations | Admin |
```

## API

Main endpoints:

```text
GET    /api/v1/organizations
GET    /api/v1/projects?organization_id={organization_id}
POST   /api/v1/projects
GET    /api/v1/projects/{project_id}
PATCH  /api/v1/projects/{project_id}
DELETE /api/v1/projects/{project_id}

GET    /api/v1/projects/{project_id}/boards
POST   /api/v1/projects/{project_id}/boards
GET    /api/v1/boards/{board_id}
PATCH  /api/v1/boards/{board_id}
DELETE /api/v1/boards/{board_id}

GET    /api/v1/boards/{board_id}/columns
POST   /api/v1/boards/{board_id}/columns
PATCH  /api/v1/columns/{column_id}
DELETE /api/v1/columns/{column_id}

GET    /api/v1/organizations/{organization_id}/invitations
POST   /api/v1/organizations/{organization_id}/invitations
POST   /api/v1/invitations/{invitation_id}/revoke
```

## Running Locally
### Backend
```bash
cd backend
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8010
```
### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5174
```

### Quality checks

Backend:
```bash
cd backend
uv run ruff format .
uv run ruff check .
uv run mypy app
uv run pytest -v
```

Frontend:
```bash
cd frontend
npm run lint
npm run test -- --run
npm run build
```