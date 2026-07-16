from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import WebSocket

from app.core.logging import logger


class ConnectionManager:
    """In-process registry for board and user WebSocket connections."""

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._user_rooms: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(
        self,
        board_id: str,
        websocket: WebSocket,
    ) -> None:
        """Connect a socket to a board-scoped room."""
        await websocket.accept()

        async with self._lock:
            self._rooms[board_id].add(websocket)
            room_size = len(self._rooms[board_id])

        logger.info(
            "ws_connected",
            board_id=board_id,
            room_size=room_size,
        )

    async def disconnect(
        self,
        board_id: str,
        websocket: WebSocket,
    ) -> None:
        """Disconnect a socket from a board-scoped room."""
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
        """Broadcast a message to a board-scoped room."""
        async with self._lock:
            targets = list(self._rooms.get(board_id, set()))

        dead = await self._send_to_connections(targets, message)

        if dead:
            async with self._lock:
                room = self._rooms.get(board_id)

                if room is not None:
                    for connection in dead:
                        room.discard(connection)

                    if not room:
                        self._rooms.pop(board_id, None)

    async def connect_user(
        self,
        user_id: str,
        websocket: WebSocket,
    ) -> None:
        """Connect a socket to an authenticated user's private room."""
        await websocket.accept()

        async with self._lock:
            self._user_rooms[user_id].add(websocket)
            room_size = len(self._user_rooms[user_id])

        logger.info(
            "user_ws_connected",
            user_id=user_id,
            room_size=room_size,
        )

    async def disconnect_user(
        self,
        user_id: str,
        websocket: WebSocket,
    ) -> None:
        """Disconnect a socket from a user's private room."""
        async with self._lock:
            room = self._user_rooms.get(user_id)

            if room is not None:
                room.discard(websocket)

                if not room:
                    self._user_rooms.pop(user_id, None)

        logger.info("user_ws_disconnected", user_id=user_id)

    async def broadcast_to_user(
        self,
        user_id: str,
        message: str,
    ) -> None:
        """Broadcast a message only to one authenticated user."""
        async with self._lock:
            targets = list(self._user_rooms.get(user_id, set()))

        dead = await self._send_to_connections(targets, message)

        if dead:
            async with self._lock:
                room = self._user_rooms.get(user_id)

                if room is not None:
                    for connection in dead:
                        room.discard(connection)

                    if not room:
                        self._user_rooms.pop(user_id, None)

    @staticmethod
    async def _send_to_connections(
        targets: list[WebSocket],
        message: str,
    ) -> list[WebSocket]:
        dead: list[WebSocket] = []

        for connection in targets:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)

        return dead


connection_manager = ConnectionManager()
