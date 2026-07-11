import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
    ) -> list[Project]:
        result = await self.session.execute(
            select(Project)
            .where(Project.organization_id == organization_id)
            .order_by(Project.created_at.asc()),
        )
        return list(result.scalars().all())

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        result = await self.session.execute(
            select(Project).where(Project.id == project_id),
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        organization_id: uuid.UUID,
        name: str,
        description: str | None,
    ) -> Project:
        project = Project(
            organization_id=organization_id,
            name=name,
            description=description,
        )
        self.session.add(project)
        await self.session.flush()
        return project

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
