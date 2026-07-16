from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: NotificationType
    title: str
    body: str
    board_id: uuid.UUID | None
    card_id: uuid.UUID | None
    is_read: bool
    created_at: datetime


class UnreadCount(BaseModel):
    unread_count: int
