# CI/CD & End-to-End Testing

## Pipeline (`.github/workflows/ci.yml`)

The pipeline runs on every push to `main`, every pull request, and on version
tags. Jobs, in dependency order:

1. **backend-quality** — `ruff format --check`, `ruff check`, `mypy app`.
2. **backend-tests** — spins up Postgres and Redis service containers, runs
   `alembic upgrade head`, then `pytest` with coverage. Coverage XML is
   uploaded as an artifact.
3. **frontend-quality-tests** — `npm run lint`, `vitest --run --coverage`,
   `npm run build`.
4. **e2e** — builds and starts the full `docker-compose.yml` stack, waits for
   `/health` through Nginx, then runs Playwright against `http://localhost:8080`.
   The Playwright HTML report and (on failure) compose logs are uploaded.
5. **publish-images** — only on `main` and version tags. Builds the backend and
   frontend images and pushes them to GHCR
   (`ghcr.io/<owner>/<repo>/backend`, `.../frontend`) tagged by branch, commit
   SHA, and semver. A `v1.0.0` git tag therefore publishes `1.0.0`-tagged
   images.

`concurrency` cancels superseded runs on the same ref. GHA build cache
(`type=gha`) speeds up image builds.

## Why the E2E stage builds the real Compose stack

The Playwright scenario exercises the production topology end to end: the React
build served by Nginx, REST proxied to FastAPI, and the WebSocket upgrade
proxied through `/api/v1/ws`. Testing against the same stack users run catches
proxy, CORS, and same-origin issues that unit tests cannot.

## E2E scenario

`e2e/tests/kanban-realtime.spec.ts`:

1. Register a user (auto-creates an organization).
2. Create a project and a board.
3. Create a card.
4. Open a second browser context on the same board.
5. Drag the card to another column in the first context.
6. Assert the move appears in the second context **without a page refresh**,
   proving the real-time WebSocket path works through Nginx.

Deterministic selection relies on `data-testid` attributes on columns and
cards. dnd-kit requires incremental mouse moves, so the drag uses stepped
`mouse.move` calls rather than a single `dragTo`.

## Running E2E locally

```bash
docker compose up -d --build
cd e2e
npm ci
npx playwright install --with-deps chromium
E2E_BASE_URL=http://localhost:8080 npx playwright test
npx playwright show-report
```

## Coverage
- Backend: `pytest --cov=app --cov-report=xml` (config in `pyproject.toml`).
- Frontend: `vitest --coverage` (v8 provider, lcov + html).

## Design decision: images-to-GHCR as the deploy artifact
This project publishes versioned images to GHCR rather than deploying to a live
host, keeping the pipeline reproducible and host-agnostic. Any environment can
pull `ghcr.io/<owner>/<repo>/{backend,frontend}:1.0.0` and run them with the
provided `docker-compose.yml`. A concrete deploy job (SSH/k8s) can be appended
after `publish-images` when a target environment exists.

