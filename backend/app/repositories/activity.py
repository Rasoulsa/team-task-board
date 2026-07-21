from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
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

    async def list_for_board(
        self,
        *,
        board_id: uuid.UUID,
        limit: int,
        cursor: tuple[datetime, str] | None,
    ) -> list[ActivityLog]:
        """Cursor keyset pagination. Fetches limit+1 to detect a next page.

        actor is eager-loaded via the relationship's lazy='joined'.
        """
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.board_id == board_id)
            .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
            .limit(limit + 1)
        )

        if cursor is not None:
            cursor_ts, cursor_id = cursor
            stmt = stmt.where(
                or_(
                    ActivityLog.created_at < cursor_ts,
                    and_(
                        ActivityLog.created_at == cursor_ts,
                        ActivityLog.id < uuid.UUID(cursor_id),
                    ),
                )
            )

        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())
