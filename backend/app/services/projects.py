import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rbac import require_org_role
from app.models.enums import OrganizationRole
from app.models.project import Project
from app.models.user import User
from app.repositories.projects import ProjectRepository


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.projects = ProjectRepository(session)

    async def list_projects(
        self,
        *,
        organization_id: uuid.UUID,
        current_user: User,
    ) -> list[Project]:
        await require_org_role(
            session=self.session,
            organization_id=organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.VIEWER,
        )
        return await self.projects.list_by_organization(organization_id)

    async def get_project(
        self,
        *,
        project_id: uuid.UUID,
        current_user: User,
    ) -> Project:
        project = await self.projects.get_by_id(project_id)
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
        return project

    async def create_project(
        self,
        *,
        organization_id: uuid.UUID,
        name: str,
        description: str | None,
        current_user: User,
    ) -> Project:
        await require_org_role(
            session=self.session,
            organization_id=organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.MEMBER,
        )

        project = await self.projects.create(
            organization_id=organization_id,
            name=name,
            description=description,
        )

        await self.session.commit()
        await self.session.refresh(project)

        return project

    async def update_project(
        self,
        *,
        project_id: uuid.UUID,
        name: str | None,
        description: str | None,
        current_user: User,
    ) -> Project:
        project = await self.get_project(
            project_id=project_id,
            current_user=current_user,
        )

        await require_org_role(
            session=self.session,
            organization_id=project.organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.MEMBER,
        )

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description

        await self.session.commit()
        await self.session.refresh(project)

        return project

    async def delete_project(
        self,
        *,
        project_id: uuid.UUID,
        current_user: User,
    ) -> None:
        project = await self.get_project(
            project_id=project_id,
            current_user=current_user,
        )

        await require_org_role(
            session=self.session,
            organization_id=project.organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.ADMIN,
        )

        await self.projects.delete(project)
        await self.session.commit()
