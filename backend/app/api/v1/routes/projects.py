import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.projects import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    organization_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectRead]:
    service = ProjectService(session)
    projects = await service.list_projects(
        organization_id=organization_id,
        current_user=current_user,
    )
    return [ProjectRead.model_validate(project) for project in projects]


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    service = ProjectService(session)
    project = await service.create_project(
        organization_id=payload.organization_id,
        name=payload.name,
        description=payload.description,
        current_user=current_user,
    )
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    service = ProjectService(session)
    project = await service.get_project(
        project_id=project_id,
        current_user=current_user,
    )
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    service = ProjectService(session)
    project = await service.update_project(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        current_user=current_user,
    )
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = ProjectService(session)
    await service.delete_project(
        project_id=project_id,
        current_user=current_user,
    )
