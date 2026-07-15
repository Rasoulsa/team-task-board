from __future__ import annotations

from uuid import UUID

import jwt

from app.core.security import decode_token


class WebSocketAuthError(Exception):
    pass


def authenticate_ws_token(token: str | None) -> UUID:
    """Validate an access token from the WS handshake and return user id."""
    if not token:
        raise WebSocketAuthError("Missing token")

    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise WebSocketAuthError("Invalid token") from exc

    if payload.get("type") != "access":
        raise WebSocketAuthError("Invalid token type")

    subject = payload.get("sub")

    if not subject:
        raise WebSocketAuthError("Invalid token subject")

    try:
        return UUID(str(subject))
    except ValueError as exc:
        raise WebSocketAuthError("Invalid token subject") from exc
