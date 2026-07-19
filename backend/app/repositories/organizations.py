from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import OrganizationRole
from app.models.org_member import OrgMember
from app.models.organization import Organization
from app.models.user import User


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(
        self,
        user_id: UUID,
    ) -> list[tuple[Organization, OrganizationRole]]:
        """
        List all organizations for a user (excluding guest memberships).
        Returns tuples of (organization, role) so callers can see the user's role per org.
        """
        statement = (
            select(Organization, OrgMember.role)
            .join(
                OrgMember,
                OrgMember.organization_id == Organization.id,
            )
            .where(
                OrgMember.user_id == user_id,
                OrgMember.role != OrganizationRole.GUEST,
            )
            .order_by(Organization.created_at.asc())
        )

        result = await self.session.execute(statement)
        return list(result.all())

    async def get_member(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> OrgMember | None:
        statement = select(OrgMember).where(
            OrgMember.organization_id == organization_id,
            OrgMember.user_id == user_id,
        )

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_members(
        self,
        organization_id: UUID,
    ) -> list[OrgMember]:
        statement = (
            select(OrgMember)
            .options(selectinload(OrgMember.user))
            .join(OrgMember.user)
            .where(OrgMember.organization_id == organization_id)
            .order_by(User.full_name.asc(), User.email.asc())
        )

        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def add_member(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
        role: OrganizationRole = OrganizationRole.MEMBER,
    ) -> OrgMember:
        member = OrgMember(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
        )

        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)

        return member