import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rbac import require_org_role
from app.models.board import Board
from app.models.enums import OrganizationRole
from app.models.org_member import OrgMember
from app.models.user import User
from app.repositories.boards import BoardRepository
from app.repositories.columns import ColumnRepository
from app.repositories.organizations import OrganizationRepository
from app.repositories.projects import ProjectRepository

DEFAULT_COLUMN_NAMES = ["To Do", "In Progress", "Done"]


class BoardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.boards = BoardRepository(session)
        self.projects = ProjectRepository(session)
        self.columns = ColumnRepository(session)
        self.organizations = OrganizationRepository(session)

    async def list_boards(
        self,
        *,
        project_id: uuid.UUID,
        current_user: User,
    ) -> list[Board]:
        project = await self.projects.get_by_id(project_id)

        if project is None:
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

        return await self.boards.list_by_project(project_id)

    async def get_board(
        self,
        *,
        board_id: uuid.UUID,
        current_user: User,
    ) -> Board:
        board = await self.boards.get_by_id(board_id)

        if board is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found",
            )

        project = await self.projects.get_by_id(board.project_id)

        if project is None:
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

        return board

    async def create_board(
        self,
        *,
        project_id: uuid.UUID,
        name: str,
        description: str | None,
        current_user: User,
    ) -> Board:
        project = await self.projects.get_by_id(project_id)

        if project is None:
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

        board = await self.boards.create(
            project_id=project_id,
            name=name,
            description=description,
        )

        for position, column_name in enumerate(DEFAULT_COLUMN_NAMES):
            await self.columns.create(
                board_id=board.id,
                name=column_name,
                position=position,
                is_done_column=(position == len(DEFAULT_COLUMN_NAMES) - 1),
            )

        await self.session.commit()
        await self.session.refresh(board)

        return board

    async def update_board(
        self,
        *,
        board_id: uuid.UUID,
        name: str | None,
        description: str | None,
        current_user: User,
    ) -> Board:
        board = await self.get_board(
            board_id=board_id,
            current_user=current_user,
        )

        project = await self.projects.get_by_id(board.project_id)

        if project is None:
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
            board.name = name

        if description is not None:
            board.description = description

        await self.session.commit()
        await self.session.refresh(board)

        return board

    async def delete_board(
        self,
        *,
        board_id: uuid.UUID,
        current_user: User,
    ) -> None:
        board = await self.get_board(
            board_id=board_id,
            current_user=current_user,
        )

        project = await self.projects.get_by_id(board.project_id)

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        await require_org_role(
            session=self.session,
            organization_id=project.organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.ADMIN,
        )

        await self.boards.delete(board)
        await self.session.commit()

    async def get_kanban_board(
        self,
        *,
        board_id: uuid.UUID,
        current_user: User,
    ) -> Board:
        await self.get_board(
            board_id=board_id,
            current_user=current_user,
        )

        board = await self.boards.get_kanban(board_id)

        if board is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found",
            )

        return board

    async def list_members(
        self,
        *,
        board_id: uuid.UUID,
        current_user: User,
    ) -> list[OrgMember]:
        board = await self.get_board(
            board_id=board_id,
            current_user=current_user,
        )

        project = await self.projects.get_by_id(board.project_id)

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        return await self.organizations.list_members(
            project.organization_id,
        )
