from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.board import Board
from app.models.board_column import BoardColumn
from app.models.card import Card
from app.models.project import Project


async def get_board_and_org_for_column(
    session: AsyncSession,
    column_id: uuid.UUID,
) -> tuple[uuid.UUID, uuid.UUID]:
    stmt = (
        select(Board.id, Project.organization_id)
        .join(BoardColumn, BoardColumn.board_id == Board.id)
        .join(Project, Project.id == Board.project_id)
        .where(BoardColumn.id == column_id)
    )
    result = await session.execute(stmt)
    row = result.first()

    if row is None:
        raise NotFoundException("Column not found")

    return row[0], row[1]


async def get_board_and_org_for_card(
    session: AsyncSession,
    card_id: uuid.UUID,
) -> tuple[uuid.UUID, uuid.UUID]:
    stmt = (
        select(Board.id, Project.organization_id)
        .join(BoardColumn, BoardColumn.board_id == Board.id)
        .join(Card, Card.column_id == BoardColumn.id)
        .join(Project, Project.id == Board.project_id)
        .where(Card.id == card_id)
    )
    result = await session.execute(stmt)
    row = result.first()

    if row is None:
        raise NotFoundException("Card not found")

    return row[0], row[1]


async def get_org_for_board(
    session: AsyncSession,
    board_id: uuid.UUID,
) -> uuid.UUID:
    stmt = (
        select(Project.organization_id)
        .join(Board, Board.project_id == Project.id)
        .where(Board.id == board_id)
    )
    result = await session.execute(stmt)
    org_id = result.scalar_one_or_none()

    if org_id is None:
        raise NotFoundException("Board not found")

    return org_id
