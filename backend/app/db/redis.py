from redis.asyncio import Redis

from app.core.config import settings


def create_redis_client() -> Redis:
    """Create an application Redis client.

    The caller is responsible for closing it with ``await client.aclose()``.
    """
    return Redis.from_url(settings.REDIS_URL)
