from __future__ import annotations

import uuid

from app.models.notification import Notification
from app.repositories.notifications import NotificationRepository


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self._repository = repository

    async def list(
        self,
        user_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Notification]:
        return await self._repository.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
        )

    async def unread_count(self, user_id: uuid.UUID) -> int:
        return await self._repository.unread_count(user_id)

    async def mark_read(
        self,
        user_id: uuid.UUID,
        notification_id: uuid.UUID,
    ) -> None:
        await self._repository.mark_read(user_id, notification_id)

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        await self._repository.mark_all_read(user_id)
