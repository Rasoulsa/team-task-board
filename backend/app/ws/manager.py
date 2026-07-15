from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import WebSocket

from app.core.logging import logger


class ConnectionManager:
    """In-process registry of WebSocket connections grouped by board."""

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(
        self,
        board_id: str,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        async with self._lock:
            self._rooms[board_id].add(websocket)

        logger.info(
            "ws_connected",
            board_id=board_id,
            room_size=len(self._rooms[board_id]),
        )

    async def disconnect(
        self,
        board_id: str,
        websocket: WebSocket,
    ) -> None:
        async with self._lock:
            room = self._rooms.get(board_id)

            if room is not None:
                room.discard(websocket)

                if not room:
                    self._rooms.pop(board_id, None)

        logger.info("ws_disconnected", board_id=board_id)

    async def broadcast(
        self,
        board_id: str,
        message: str,
    ) -> None:
        async with self._lock:
            targets = list(self._rooms.get(board_id, set()))

        dead: list[WebSocket] = []

        for connection in targets:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)

        if dead:
            async with self._lock:
                room = self._rooms.get(board_id)

                if room is not None:
                    for connection in dead:
                        room.discard(connection)


connection_manager = ConnectionManager()
