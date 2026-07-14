import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.board import Board
from app.models.board_column import BoardColumn
from app.models.card import Card


class BoardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_project(self, project_id: uuid.UUID) -> list[Board]:
        result = await self.session.execute(
            select(Board).where(Board.project_id == project_id).order_by(Board.created_at.asc()),
        )
        return list(result.scalars().all())

    async def get_by_id(self, board_id: uuid.UUID) -> Board | None:
        result = await self.session.execute(
            select(Board).where(Board.id == board_id),
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        project_id: uuid.UUID,
        name: str,
        description: str | None,
    ) -> Board:
        board = Board(
            project_id=project_id,
            name=name,
            description=description,
        )
        self.session.add(board)
        await self.session.flush()
        return board

    async def delete(self, board: Board) -> None:
        await self.session.delete(board)

    async def get_kanban(self, board_id: uuid.UUID) -> Board | None:
        statement = (
            select(Board)
            .where(Board.id == board_id)
            .options(
                selectinload(Board.columns)
                .selectinload(BoardColumn.cards)
                .selectinload(Card.labels),
                selectinload(Board.columns)
                .selectinload(BoardColumn.cards)
                .selectinload(Card.assignees),
                selectinload(Board.columns)
                .selectinload(BoardColumn.cards)
                .selectinload(Card.checklist_items),
            )
        )

        result = await self.session.execute(statement)
        board = result.unique().scalar_one_or_none()

        if board is None:
            return None

        # BoardColumn is ordered by integer `position`.
        board.columns.sort(key=lambda column: column.position)

        for column in board.columns:
            active_cards = [card for card in column.cards if not getattr(card, "is_deleted", False)]
            # Cards use LexoRank string ordering.
            active_cards.sort(key=lambda card: card.rank)
            column.cards = active_cards

        return board
