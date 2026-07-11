import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rbac import require_org_role
from app.models.enums import InvitationStatus, OrganizationRole
from app.models.invitation import Invitation
from app.models.user import User


class InvitationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_invitations(
        self,
        *,
        organization_id: uuid.UUID,
        current_user: User,
    ) -> list[Invitation]:
        await require_org_role(
            session=self.session,
            organization_id=organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.ADMIN,
        )

        result = await self.session.execute(
            select(Invitation)
            .where(Invitation.organization_id == organization_id)
            .order_by(Invitation.created_at.desc()),
        )
        return list(result.scalars().all())

    async def create_invitation(
        self,
        *,
        organization_id: uuid.UUID,
        email: str,
        role: OrganizationRole,
        current_user: User,
    ) -> Invitation:
        await require_org_role(
            session=self.session,
            organization_id=organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.ADMIN,
        )

        if role == OrganizationRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot invite users as owner",
            )

        invitation = Invitation(
            organization_id=organization_id,
            inviter_id=current_user.id,
            email=email,
            token=secrets.token_urlsafe(32),
            role=role,
            status=InvitationStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )

        self.session.add(invitation)
        await self.session.commit()
        await self.session.refresh(invitation)

        return invitation

    async def revoke_invitation(
        self,
        *,
        invitation_id: uuid.UUID,
        current_user: User,
    ) -> None:
        invitation = await self.session.get(Invitation, invitation_id)
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        await require_org_role(
            session=self.session,
            organization_id=invitation.organization_id,
            current_user=current_user,
            minimum_role=OrganizationRole.ADMIN,
        )

        invitation.status = InvitationStatus.REVOKED

        await self.session.commit()
