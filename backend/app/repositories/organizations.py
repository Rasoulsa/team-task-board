import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_member import OrgMember
from app.models.organization import Organization


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: uuid.UUID) -> list[Organization]:
        result = await self.session.execute(
            select(Organization)
            .join(OrgMember, OrgMember.organization_id == Organization.id)
            .where(OrgMember.user_id == user_id)
            .order_by(Organization.created_at.asc()),
        )
        return list(result.scalars().all())
