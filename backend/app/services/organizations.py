import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rbac import require_org_role
from app.models.enums import OrganizationRole
from app.models.org_member import OrgMember
from app.models.organization import Organization
from app.models.user import User
from app.repositories.organizations import OrganizationRepository


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.organizations = OrganizationRepository(session)

    async def list_my_organizations(
        self,
        current_user: User,
    ) -> list[tuple[Organization, OrganizationRole]]:
        """
        List all organizations for the current user with their role in each.
        Returns list of (Organization, role) tuples.
        """
        return await self.organizations.list_for_user(current_user.id)

    async def list_members(
        self,
        *,
        organization_id: uuid.UUID,
        current_user: User,
    ) -> list[OrgMember]:
        await require_org_role(
            session=self.session,
            organization_id=organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.VIEWER,
        )

        return await self.organizations.list_members(
            organization_id,
        )