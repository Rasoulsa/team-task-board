from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.exceptions import (
    app_exception_handler as handle_app_exception,
)
from app.core.logging import configure_logging, logger
from app.db.redis import create_redis_client
from app.db.session import engine
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
        title=settings.APP_NAME,
        version="1.0.0",
        lifespan=lifespan,
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

    return app


app = create_app()
