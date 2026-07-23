from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from redis.asyncio import Redis
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.exceptions import (
    app_exception_handler as handle_app_exception,
)
from app.core.logging import configure_logging, logger
from app.db.redis import create_redis_client
from app.db.session import AsyncSessionLocal, engine
from app.ws.manager import connection_manager
from app.ws.presence import PresenceTracker
from app.ws.pubsub import RedisEventBridge
from app.ws.router import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()

    redis_client = create_redis_client()
    app.state.redis = redis_client

    try:
        await redis_client.ping()
    except Exception:
        logger.exception(
            "redis_connection_failed",
            redis_url=settings.REDIS_URL,
        )
        await redis_client.aclose()
        raise

    event_bridge = RedisEventBridge(redis_client, connection_manager)
    presence = PresenceTracker(redis_client)

    await event_bridge.start()

    app.state.event_bridge = event_bridge
    app.state.presence = presence

    logger.info("startup", app=settings.APP_NAME, env=settings.ENV)

    try:
        yield
    finally:
        await event_bridge.stop()
        await redis_client.aclose()
        await engine.dispose()
        logger.info("shutdown")


async def registered_app_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    assert isinstance(exc, AppException)
    return await handle_app_exception(request, exc)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Team Task Board API",
        description=(
            "Real-time Trello-style task management platform.\n\n"
            "Organizations, projects, boards, LexoRank-ordered cards, comments, "
            "RBAC, WebSocket live updates, Celery notifications, and reporting."
        ),
        version="1.0.0",
        lifespan=lifespan,
        openapi_tags=[
            {
                "name": "auth",
                "description": "Registration, login, refresh rotation, password reset.",
            },
            {"name": "organizations", "description": "Organizations and invitations."},
            {"name": "projects", "description": "Project CRUD within an organization."},
            {"name": "boards", "description": "Boards and columns."},
            {
                "name": "cards",
                "description": "Cards, ordering, labels, assignees, checklists, comments.",
            },
            {"name": "activity", "description": "Board activity feed (cursor-paginated)."},
            {"name": "reporting", "description": "Board stats and aggregates."},
            {"name": "notifications", "description": "In-app notifications and unread counts."},
            {
                "name": "ws",
                "description": "WebSocket endpoints for real-time board and notification events.",
            },
            {"name": "health", "description": "Liveness and readiness probes."},
        ],
        contact={"name": "Team Task Board", "url": "https://github.com/Rasoulsa/team-task-board"},
        license_info={"name": "See LICENSE"},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(
        AppException,
        registered_app_exception_handler,
    )

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def readiness(request: Request) -> JSONResponse:
        """Readiness: verify DB + Redis are reachable."""
        checks: dict[str, str] = {}
        healthy = True

        redis: Redis = request.app.state.redis
        try:
            await redis.ping()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "unavailable"
            healthy = False

        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "unavailable"
            healthy = False

        return JSONResponse(
            status_code=200 if healthy else 503,
            content={"status": "ready" if healthy else "degraded", "checks": checks},
        )

    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics", "/health"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    return app


app = create_app()
