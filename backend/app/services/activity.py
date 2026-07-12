from __future__ import annotations

import uuid

from app.models.activity import ActivityLog
from app.repositories.activity import ActivityRepository


class ActivityService:
    def __init__(self, repository: ActivityRepository) -> None:
        self.repository = repository

    async def record(
        self,
        board_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        meta: dict | None = None,
    ) -> ActivityLog:
        log = ActivityLog(
            board_id=board_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            meta=meta or {},
        )
        return await self.repository.create(log)

    async def list_board_activity(
        self,
        board_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ActivityLog]:
        return await self.repository.list_by_board(board_id, limit=limit)
