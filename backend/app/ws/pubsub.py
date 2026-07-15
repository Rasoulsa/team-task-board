from __future__ import annotations

import asyncio
from contextlib import suppress

from redis.asyncio import Redis

from app.core.logging import logger
from app.ws.events import RealtimeEvent
from app.ws.manager import ConnectionManager


class RedisEventBridge:
    """Bridges Redis Pub/Sub messages to local WebSocket rooms."""

    def __init__(
        self,
        redis: Redis,
        manager: ConnectionManager,
    ) -> None:
        self._redis = redis
        self._manager = manager
        self._pubsub = redis.pubsub()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        await self._pubsub.psubscribe("board:*")
        self._task = asyncio.create_task(self._listen())
        logger.info("event_bridge_started")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()

            with suppress(asyncio.CancelledError):
                await self._task

            self._task = None

        await self._pubsub.punsubscribe("board:*")
        await self._pubsub.aclose()
        logger.info("event_bridge_stopped")

    async def publish(self, event: RealtimeEvent) -> None:
        channel = RealtimeEvent.channel_for(event.board_id)
        await self._redis.publish(channel, event.to_json())

    async def _listen(self) -> None:
        async for message in self._pubsub.listen():
            if message is None:
                continue

            if message.get("type") != "pmessage":
                continue

            data = message.get("data")

            if data is None:
                continue

            try:
                event = RealtimeEvent.from_json(data)
            except Exception:
                logger.exception("event_bridge_parse_failed")
                continue

            await self._manager.broadcast(
                event.board_id,
                event.to_json(),
            )
