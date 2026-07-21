import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.board_column import BoardColumn


class ColumnRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_board(self, board_id: uuid.UUID) -> list[BoardColumn]:
        result = await self.session.execute(
            select(BoardColumn)
            .where(BoardColumn.board_id == board_id)
            .order_by(BoardColumn.position.asc()),
        )
        return list(result.scalars().all())

    async def get_by_id(self, column_id: uuid.UUID) -> BoardColumn | None:
        result = await self.session.execute(
            select(BoardColumn).where(BoardColumn.id == column_id),
        )
        return result.scalar_one_or_none()

    async def get_next_position(self, board_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.max(BoardColumn.position)).where(
                BoardColumn.board_id == board_id,
            ),
        )
        max_position = result.scalar_one_or_none()
        if max_position is None:
            return 0
        return int(max_position) + 1

    async def create(
        self,
        *,
        board_id: uuid.UUID,
        name: str,
        position: int,
        is_done_column: bool = False,
    ) -> BoardColumn:
        column = BoardColumn(
            board_id=board_id,
            name=name,
            position=position,
            is_done_column=is_done_column,
        )
        self.session.add(column)
        await self.session.flush()
        return column

    async def delete(self, column: BoardColumn) -> None:
        await self.session.delete(column)
