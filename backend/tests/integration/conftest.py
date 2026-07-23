from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import AsyncClient

from app.main import app


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clear_auth_rate_limits(
    async_client: AsyncClient,
) -> AsyncIterator[None]:
    """Clear authentication rate-limit state between integration tests."""

    redis = app.state.redis

    keys = [key async for key in redis.scan_iter(match="rate-limit:auth:*")]

    if keys:
        await redis.delete(*keys)

    yield

    keys = [key async for key in redis.scan_iter(match="rate-limit:auth:*")]

    if keys:
        await redis.delete(*keys)