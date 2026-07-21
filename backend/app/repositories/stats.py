from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models.board_column import BoardColumn
from app.models.card import Card, CardAssignee
from app.models.org_member import OrgMember
from app.models.user import User


@dataclass(frozen=True)
class MemberStatsRow:
    user_id: uuid.UUID
    full_name: str
    email: str
    open_count: int
    closed_count: int
    overdue_count: int


@dataclass(frozen=True)
class BoardTotals:
    open_count: int
    closed_count: int
    overdue_count: int
    total_count: int


class StatsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _has_done_flag(self, board_id: uuid.UUID) -> bool:
        """True if any column on the board is explicitly flagged done."""
        result = await self.session.execute(
            select(func.count(BoardColumn.id)).where(
                BoardColumn.board_id == board_id,
                BoardColumn.is_done_column.is_(True),
            )
        )
        return (result.scalar_one() or 0) > 0

    async def _max_position(self, board_id: uuid.UUID) -> int | None:
        result = await self.session.execute(
            select(func.max(BoardColumn.position)).where(BoardColumn.board_id == board_id)
        )
        return result.scalar_one_or_none()

    async def _done_predicate(self, board_id: uuid.UUID) -> ColumnElement[bool]:
        """Return a SQL boolean expr identifying a 'done' column.

        Primary: explicit is_done_column flag. Fallback: highest position.
        """
        if await self._has_done_flag(board_id):
            return BoardColumn.is_done_column.is_(True)
        max_pos = await self._max_position(board_id)
        if max_pos is None:
            return BoardColumn.position < 0  # matches nothing
        return BoardColumn.position == max_pos

    async def member_stats(
        self,
        *,
        board_id: uuid.UUID,
        organization_id: uuid.UUID,
        now: datetime,
    ) -> list[MemberStatsRow]:
        """Per-member open/closed/overdue in one grouped query. No N+1.

        LEFT joins from OrgMember so members with zero cards still appear.
        """
        is_done = await self._done_predicate(board_id)
        not_done = ~is_done

        active = Card.is_deleted.is_(False)

        open_expr = func.count(case((and_(active, not_done), Card.id)))
        closed_expr = func.count(case((and_(active, is_done), Card.id)))
        overdue_expr = func.count(
            case(
                (
                    and_(
                        active,
                        not_done,
                        Card.due_date.is_not(None),
                        Card.due_date < now,
                    ),
                    Card.id,
                )
            )
        )

        board_columns_subq = select(BoardColumn.id).where(BoardColumn.board_id == board_id)

        stmt = (
            select(
                User.id,
                User.full_name,
                User.email,
                open_expr.label("open_count"),
                closed_expr.label("closed_count"),
                overdue_expr.label("overdue_count"),
            )
            .select_from(OrgMember)
            .join(User, User.id == OrgMember.user_id)
            .join(
                CardAssignee,
                CardAssignee.user_id == OrgMember.user_id,
                isouter=True,
            )
            .join(
                Card,
                and_(
                    Card.id == CardAssignee.card_id,
                    Card.column_id.in_(board_columns_subq),
                ),
                isouter=True,
            )
            .join(BoardColumn, BoardColumn.id == Card.column_id, isouter=True)
            .where(OrgMember.organization_id == organization_id)
            .group_by(User.id, User.full_name, User.email)
            .order_by(User.full_name.asc())
        )

        result = await self.session.execute(stmt)
        return [
            MemberStatsRow(
                user_id=row.id,
                full_name=row.full_name,
                email=row.email,
                open_count=int(row.open_count or 0),
                closed_count=int(row.closed_count or 0),
                overdue_count=int(row.overdue_count or 0),
            )
            for row in result.all()
        ]

    async def board_totals(
        self,
        *,
        board_id: uuid.UUID,
        now: datetime,
    ) -> BoardTotals:
        """Board-wide totals; each card counted once."""
        is_done = await self._done_predicate(board_id)
        not_done = ~is_done
        active = Card.is_deleted.is_(False)

        stmt = (
            select(
                func.count(case((and_(active, not_done), Card.id))).label("open"),
                func.count(case((and_(active, is_done), Card.id))).label("closed"),
                func.count(
                    case(
                        (
                            and_(
                                active,
                                not_done,
                                Card.due_date.is_not(None),
                                Card.due_date < now,
                            ),
                            Card.id,
                        )
                    )
                ).label("overdue"),
                func.count(case((active, Card.id))).label("total"),
            )
            .select_from(Card)
            .join(BoardColumn, BoardColumn.id == Card.column_id)
            .where(BoardColumn.board_id == board_id)
        )

        row = (await self.session.execute(stmt)).one()
        return BoardTotals(
            open_count=int(row.open or 0),
            closed_count=int(row.closed or 0),
            overdue_count=int(row.overdue or 0),
            total_count=int(row.total or 0),
        )
