import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.organization import (
    OrganizationMemberRead,
    OrganizationRead,
)
from app.services.organizations import OrganizationService

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
)


@router.get(
    "",
    response_model=list[OrganizationRead],
)
async def list_my_organizations(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrganizationRead]:
    service = OrganizationService(session)
    memberships = await service.list_my_organizations(current_user)

    # memberships is now list[tuple[Organization, OrganizationRole]]
    return [
        OrganizationRead(
            id=organization.id,
            name=organization.name,
            role=role,
            created_at=organization.created_at,
            updated_at=organization.updated_at,
        )
        for organization, role in memberships
    ]


@router.get(
    "/{organization_id}/members",
    response_model=list[OrganizationMemberRead],
)
async def list_organization_members(
    organization_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrganizationMemberRead]:
    service = OrganizationService(session)
    members = await service.list_members(
        organization_id=organization_id,
        current_user=current_user,
    )

    return [
        OrganizationMemberRead(
            id=member.id,
            user_id=member.user_id,
            organization_id=member.organization_id,
            full_name=member.user.full_name,
            email=member.user.email,
            role=member.role,
            created_at=member.created_at,
        )
        for member in members
    ]
