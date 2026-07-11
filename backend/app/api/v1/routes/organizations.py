from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.organization import OrganizationRead
from app.services.organizations import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationRead])
async def list_my_organizations(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrganizationRead]:
    service = OrganizationService(session)
    organizations = await service.list_my_organizations(current_user)
    return [OrganizationRead.model_validate(item) for item in organizations]
