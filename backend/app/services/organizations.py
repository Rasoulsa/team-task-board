from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.user import User
from app.repositories.organizations import OrganizationRepository


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.organizations = OrganizationRepository(session)

    async def list_my_organizations(self, current_user: User) -> list[Organization]:
        return await self.organizations.list_for_user(current_user.id)
