from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class EventType(StrEnum):
    CARD_CREATED = "card.created"
    CARD_UPDATED = "card.updated"
    CARD_MOVED = "card.moved"
    CARD_DELETED = "card.deleted"
    CARD_RESTORED = "card.restored"
    COMMENT_CREATED = "comment.created"
    PRESENCE_JOIN = "presence.join"
    PRESENCE_LEAVE = "presence.leave"

    # User-scoped notification event.
    NOTIFICATION_CREATED = "notification.created"


@dataclass(slots=True)
class RealtimeEvent:
    """An event broadcast to every connection watching a board."""

    type: EventType
    board_id: str
    actor_id: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )

    def to_json(self) -> str:
        return json.dumps(
            {
                "event_id": self.event_id,
                "type": str(self.type),
                "board_id": self.board_id,
                "actor_id": self.actor_id,
                "payload": self.payload,
                "created_at": self.created_at,
            },
        )

    @classmethod
    def from_json(cls, raw: str | bytes) -> RealtimeEvent:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        data = json.loads(raw)

        return cls(
            type=EventType(data["type"]),
            board_id=data["board_id"],
            actor_id=data["actor_id"],
            payload=data["payload"],
            event_id=data["event_id"],
            created_at=data["created_at"],
        )

    @staticmethod
    def channel_for(board_id: str) -> str:
        return f"board:{board_id}"


@dataclass(slots=True)
class UserRealtimeEvent:
    """An event delivered only to one authenticated user."""

    type: EventType
    user_id: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )

    def to_json(self) -> str:
        return json.dumps(
            {
                "event_id": self.event_id,
                "type": str(self.type),
                "user_id": self.user_id,
                "payload": self.payload,
                "created_at": self.created_at,
            },
        )

    @classmethod
    def from_json(cls, raw: str | bytes) -> UserRealtimeEvent:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        data = json.loads(raw)

        return cls(
            type=EventType(data["type"]),
            user_id=data["user_id"],
            payload=data["payload"],
            event_id=data["event_id"],
            created_at=data["created_at"],
        )

    @staticmethod
    def channel_for(user_id: str) -> str:
        return f"user:{user_id}"
