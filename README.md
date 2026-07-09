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
