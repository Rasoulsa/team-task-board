import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rbac import require_org_role
from app.models.board_column import BoardColumn
from app.models.enums import OrganizationRole
from app.models.user import User
from app.repositories.boards import BoardRepository
from app.repositories.columns import ColumnRepository
from app.repositories.projects import ProjectRepository


class ColumnService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.columns = ColumnRepository(session)
        self.boards = BoardRepository(session)
        self.projects = ProjectRepository(session)

    async def list_columns(
        self,
        *,
        board_id: uuid.UUID,
        current_user: User,
    ) -> list[BoardColumn]:
        board = await self.boards.get_by_id(board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found",
            )

        project = await self.projects.get_by_id(board.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        await require_org_role(
            session=self.session,
            organization_id=project.organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.VIEWER,
        )

        return await self.columns.list_by_board(board_id)

    async def create_column(
        self,
        *,
        board_id: uuid.UUID,
        name: str,
        position: int | None,
        current_user: User,
    ) -> BoardColumn:
        board = await self.boards.get_by_id(board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found",
            )

        project = await self.projects.get_by_id(board.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        await require_org_role(
            session=self.session,
            organization_id=project.organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.MEMBER,
        )

        final_position = position
        if final_position is None:
            final_position = await self.columns.get_next_position(board_id)

        column = await self.columns.create(
            board_id=board_id,
            name=name,
            position=final_position,
        )

        await self.session.commit()
        await self.session.refresh(column)

        return column

    async def update_column(
        self,
        *,
        column_id: uuid.UUID,
        name: str | None,
        position: int | None,
        current_user: User,
    ) -> BoardColumn:
        column = await self.columns.get_by_id(column_id)
        if not column:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Column not found",
            )

        board = await self.boards.get_by_id(column.board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found",
            )

        project = await self.projects.get_by_id(board.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        await require_org_role(
            session=self.session,
            organization_id=project.organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.MEMBER,
        )

        if name is not None:
            column.name = name
        if position is not None:
            column.position = position

        await self.session.commit()
        await self.session.refresh(column)

        return column

    async def delete_column(
        self,
        *,
        column_id: uuid.UUID,
        current_user: User,
    ) -> None:
        column = await self.columns.get_by_id(column_id)
        if not column:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Column not found",
            )

        board = await self.boards.get_by_id(column.board_id)
        if not board:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found",
            )

        project = await self.projects.get_by_id(board.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        await require_org_role(
            session=self.session,
            organization_id=project.organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.MEMBER,
        )

        await self.columns.delete(column)
        await self.session.commit()
