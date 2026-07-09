.PHONY: up down build logs migrate lint fix fmt fix-unsafe type test check backend-install fe-lint fe-test

up:
	docker compose up --build

down:
	docker compose down -v

build:
	docker compose build

logs:
	docker compose logs -f

backend-install:
	cd backend && uv sync --extra dev

migrate:
	docker compose exec backend alembic upgrade head

lint:
	cd backend && uv run ruff check .

fix:
	cd backend && uv run ruff check . --fix

fmt:
	cd backend && uv run ruff check . --fix && uv run ruff format .

fix-unsafe:
	cd backend && uv run ruff check . --fix --unsafe-fixes && uv run ruff format .

type:
	cd backend && uv run mypy app

test:
	cd backend && uv run pytest -v

check:
	cd backend && uv run ruff check . && uv run ruff format . --check && uv run mypy app && uv run pytest -v

fe-lint:
	cd frontend && npm run lint

fe-test:
	cd frontend && npm run test
