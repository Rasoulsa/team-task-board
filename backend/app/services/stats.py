from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stats import StatsRepository
from app.schemas.stats import BoardStats, BoardTotalsRead, MemberCardStats


class StatsService:
    def __init__(self, session: AsyncSession) -> None:
        self.stats = StatsRepository(session)

    async def board_stats(
        self,
        *,
        board_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> BoardStats:
        now = datetime.now(UTC)

        totals = await self.stats.board_totals(board_id=board_id, now=now)
        members = await self.stats.member_stats(
            board_id=board_id,
            organization_id=organization_id,
            now=now,
        )

        return BoardStats(
            board_id=board_id,
            totals=BoardTotalsRead(
                open_count=totals.open_count,
                closed_count=totals.closed_count,
                overdue_count=totals.overdue_count,
                total_count=totals.total_count,
            ),
            per_member=[
                MemberCardStats(
                    user_id=m.user_id,
                    full_name=m.full_name,
                    email=m.email,
                    open_count=m.open_count,
                    closed_count=m.closed_count,
                    overdue_count=m.overdue_count,
                )
                for m in members
            ],
        )
