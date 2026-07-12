from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityLog


class ActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, log: ActivityLog) -> ActivityLog:
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_by_board(
        self,
        board_id: uuid.UUID,
        limit: int = 50,
    ) -> list[ActivityLog]:
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.board_id == board_id)
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
