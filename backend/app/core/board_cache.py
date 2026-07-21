from __future__ import annotations

import uuid

from redis.asyncio import Redis

_CACHE_VERSION = "v1"
_TTL_SECONDS = 60


def _board_key(board_id: uuid.UUID) -> str:
    return f"board-state:{_CACHE_VERSION}:{board_id}"


async def get_cached_board(redis: Redis, board_id: uuid.UUID) -> str | None:
    value = await redis.get(_board_key(board_id))
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


async def set_cached_board(redis: Redis, board_id: uuid.UUID, payload_json: str) -> None:
    await redis.set(_board_key(board_id), payload_json, ex=_TTL_SECONDS)


async def invalidate_board(redis: Redis, board_id: uuid.UUID) -> None:
    await redis.delete(_board_key(board_id))
