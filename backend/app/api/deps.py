import uuid
from collections.abc import AsyncGenerator
from typing import cast

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.users import UserRepository
from app.ws.pubsub import RedisEventBridge

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async for session in get_db_session():
        yield session


async def get_redis(request: Request) -> Redis:
    """Return the Redis client owned by the current FastAPI application."""
    return cast(Redis, request.app.state.redis)


async def get_event_bridge(request: Request) -> RedisEventBridge:
    """Return the realtime event bridge owned by the FastAPI application."""
    return cast(RedisEventBridge, request.app.state.event_bridge)


async def rate_limit_auth(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> None:
    client_host = request.client.host if request.client else "unknown"
    key = f"rate-limit:auth:{client_host}:{request.url.path}"

    current_count = await redis.incr(key)

    if current_count == 1:
        await redis.expire(key, settings.AUTH_RATE_LIMIT_SECONDS)

    if current_count > settings.AUTH_RATE_LIMIT_TIMES:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    users = UserRepository(session)
    user = await users.get_by_id(uuid.UUID(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user
