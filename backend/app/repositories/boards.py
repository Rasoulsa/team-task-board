import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.board import Board


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
