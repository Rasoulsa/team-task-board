from __future__ import annotations

import asyncio
from contextlib import suppress

from redis.asyncio import Redis

from app.core.logging import logger
from app.ws.events import RealtimeEvent, UserRealtimeEvent
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
        await self._pubsub.psubscribe("board:*", "user:*")
        self._task = asyncio.create_task(self._listen())
        logger.info("event_bridge_started")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()

            with suppress(asyncio.CancelledError):
                await self._task

            self._task = None

        await self._pubsub.punsubscribe("board:*", "user:*")
        await self._pubsub.aclose()
        logger.info("event_bridge_stopped")

    async def publish(self, event: RealtimeEvent) -> None:
        """Publish a board-scoped event."""
        channel = RealtimeEvent.channel_for(event.board_id)
        await self._redis.publish(channel, event.to_json())

    async def publish_to_user(
        self,
        event: UserRealtimeEvent,
    ) -> None:
        """Publish a user-scoped event from an async application context."""
        channel = UserRealtimeEvent.channel_for(event.user_id)
        await self._redis.publish(channel, event.to_json())

    async def _listen(self) -> None:
        async for message in self._pubsub.listen():
            if message is None:
                continue

            if message.get("type") != "pmessage":
                continue

            channel = self._decode(message.get("channel"))
            data = message.get("data")

            if channel is None or data is None:
                continue

            if channel.startswith("board:"):
                await self._handle_board_event(data)
                continue

            if channel.startswith("user:"):
                await self._handle_user_event(data)

    async def _handle_board_event(
        self,
        data: str | bytes,
    ) -> None:
        try:
            event = RealtimeEvent.from_json(data)
        except Exception:
            logger.exception("board_event_parse_failed")
            return

        await self._manager.broadcast(
            event.board_id,
            event.to_json(),
        )

    async def _handle_user_event(
        self,
        data: str | bytes,
    ) -> None:
        try:
            event = UserRealtimeEvent.from_json(data)
        except Exception:
            logger.exception("user_event_parse_failed")
            return

        await self._manager.broadcast_to_user(
            event.user_id,
            event.to_json(),
        )

    @staticmethod
    def _decode(value: object) -> str | None:
        if isinstance(value, bytes):
            return value.decode("utf-8")

        if isinstance(value, str):
            return value

        return None
