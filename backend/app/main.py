from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.exceptions import app_exception_handler as handle_app_exception
from app.core.logging import configure_logging, logger
from app.db.redis import redis_client


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()

    try:
        await redis_client.ping()
    except Exception:
        logger.exception("redis_connection_failed", redis_url=settings.REDIS_URL)
        raise

    logger.info("startup", app=settings.APP_NAME, env=settings.ENV)

    yield

    await redis_client.aclose()
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

    app.add_exception_handler(AppException, registered_app_exception_handler)

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
