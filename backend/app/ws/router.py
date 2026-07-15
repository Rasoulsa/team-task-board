from __future__ import annotations

import asyncio
import contextlib
from contextlib import suppress
from uuid import UUID

from fastapi import (
    APIRouter,
    Query,
    WebSocket,
    WebSocketDisconnect,
)

from app.core.logging import logger
from app.db.session import get_db_session
from app.repositories.users import UserRepository
from app.services.boards import BoardService
from app.ws.auth import WebSocketAuthError, authenticate_ws_token
from app.ws.events import EventType, RealtimeEvent
from app.ws.manager import connection_manager

router = APIRouter()

HEARTBEAT_TIMEOUT_SECONDS = 15

# Standard WebSocket close codes.
WS_UNAUTHORIZED = 4401
WS_FORBIDDEN = 4403


async def _authorize_board_access(
    board_id: UUID,
    user_id: UUID,
) -> bool:
    """Reuse BoardService viewer-level RBAC to authorize WS access."""
    async for session in get_db_session():
        users = UserRepository(session)
        user = await users.get_by_id(user_id)

        if user is None or not user.is_active:
            return False

        board_service = BoardService(session)

        try:
            await board_service.get_board(
                board_id=board_id,
                current_user=user,
            )
        except Exception:
            return False

        return True

    return False


@router.websocket("/ws/boards/{board_id}")
async def board_socket(
    websocket: WebSocket,
    board_id: str,
    token: str | None = Query(default=None),
) -> None:
    try:
        user_id = authenticate_ws_token(token)
    except WebSocketAuthError:
        await websocket.close(code=WS_UNAUTHORIZED)
        return

    try:
        board_uuid = UUID(board_id)
    except ValueError:
        await websocket.close(code=WS_FORBIDDEN)
        return

    authorized = await _authorize_board_access(board_uuid, user_id)

    if not authorized:
        await websocket.close(code=WS_FORBIDDEN)
        return

    presence = websocket.app.state.presence
    bridge = websocket.app.state.event_bridge

    await connection_manager.connect(board_id, websocket)
    await presence.heartbeat(board_id, str(user_id))

    await bridge.publish(
        RealtimeEvent(
            type=EventType.PRESENCE_JOIN,
            board_id=board_id,
            actor_id=str(user_id),
            payload={
                "user_id": str(user_id),
                "online": await presence.online_users(board_id),
            },
        ),
    )

    try:
        while True:
            with suppress(TimeoutError):
                await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=HEARTBEAT_TIMEOUT_SECONDS,
                )

            await presence.heartbeat(board_id, str(user_id))

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ws_error", board_id=board_id)
    finally:
        await connection_manager.disconnect(board_id, websocket)
        await presence.leave(board_id, str(user_id))

        with contextlib.suppress(Exception):
            await bridge.publish(
                RealtimeEvent(
                    type=EventType.PRESENCE_LEAVE,
                    board_id=board_id,
                    actor_id=str(user_id),
                    payload={
                        "user_id": str(user_id),
                        "online": await presence.online_users(
                            board_id,
                        ),
                    },
                ),
            )
