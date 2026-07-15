from __future__ import annotations

from redis.asyncio import Redis

PRESENCE_TTL_SECONDS = 30


class PresenceTracker:
    """Tracks online users per board using a Redis hash + TTL."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, board_id: str) -> str:
        return f"presence:{board_id}"

    async def heartbeat(
        self,
        board_id: str,
        user_id: str,
    ) -> None:
        key = self._key(board_id)
        await self._redis.hset(key, user_id, "1")
        await self._redis.expire(key, PRESENCE_TTL_SECONDS)

    async def leave(
        self,
        board_id: str,
        user_id: str,
    ) -> None:
        await self._redis.hdel(self._key(board_id), user_id)

    async def online_users(self, board_id: str) -> list[str]:
        raw = await self._redis.hkeys(self._key(board_id))

        return [item.decode("utf-8") if isinstance(item, bytes) else str(item) for item in raw]
