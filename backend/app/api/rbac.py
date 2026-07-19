import uuid
from enum import IntEnum

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OrganizationRole
from app.models.org_member import OrgMember
from app.models.user import User


class RoleLevel(IntEnum):
    GUEST = 5
    VIEWER = 10
    MEMBER = 20
    ADMIN = 30
    OWNER = 40


ROLE_LEVELS: dict[OrganizationRole, RoleLevel] = {
    OrganizationRole.GUEST: RoleLevel.GUEST,
    OrganizationRole.VIEWER: RoleLevel.VIEWER,
    OrganizationRole.MEMBER: RoleLevel.MEMBER,
    OrganizationRole.ADMIN: RoleLevel.ADMIN,
    OrganizationRole.OWNER: RoleLevel.OWNER,
}


def role_allows(actual: OrganizationRole, required: OrganizationRole) -> bool:
    return ROLE_LEVELS[actual] >= ROLE_LEVELS[required]


async def get_membership(
    *,
    session: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
) -> OrgMember | None:
    result = await session.execute(
        select(OrgMember).where(
            OrgMember.organization_id == organization_id,
            OrgMember.user_id == user_id,
        ),
    )
    return result.scalar_one_or_none()


async def require_org_role(
    *,
    session: AsyncSession,
    organization_id: uuid.UUID,
    current_user: User,
    minimum_role: OrganizationRole,
) -> OrgMember:
    membership = await get_membership(
        session=session,
        organization_id=organization_id,
        user_id=current_user.id,
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization",
        )

    if not role_allows(membership.role, minimum_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return membership