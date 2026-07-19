import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.rbac import get_membership, require_org_role
from app.models.enums import InvitationStatus, OrganizationRole
from app.models.invitation import Invitation
from app.models.org_member import OrgMember
from app.models.user import User
from app.models.organization import Organization
from app.repositories.organizations import OrganizationRepository
from app.worker.tasks import notify_organization_invitation


class InvitationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.organizations = OrganizationRepository(session)

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

        statement = (
            select(Invitation)
            .where(
                Invitation.organization_id == organization_id,
            )
            .order_by(Invitation.created_at.desc())
        )

        result = await self.session.execute(statement)
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
                detail="Cannot invite a user with the owner role",
            )

        normalized_email = email.strip().lower()
        now = datetime.now(UTC)

        invited_user_result = await self.session.execute(
            select(User).where(
                func.lower(User.email) == normalized_email,
            ),
        )
        invited_user = invited_user_result.scalar_one_or_none()

        if invited_user is not None:
            existing_membership = await get_membership(
                session=self.session,
                organization_id=organization_id,
                user_id=invited_user.id,
            )

            if existing_membership is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This user is already a member of the organization",
                )

        pending_result = await self.session.execute(
            select(Invitation)
            .where(
                Invitation.organization_id == organization_id,
                func.lower(Invitation.email) == normalized_email,
                Invitation.status == InvitationStatus.PENDING,
                Invitation.expires_at > now,
            )
            .limit(1),
        )
        existing_pending = pending_result.scalar_one_or_none()

        if existing_pending is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending invitation already exists for this email",
            )

        invitation = Invitation(
            organization_id=organization_id,
            inviter_id=current_user.id,
            email=normalized_email,
            token=secrets.token_urlsafe(32),
            role=role,
            status=InvitationStatus.PENDING,
            expires_at=now + timedelta(days=7),
            accepted_at=None,
        )

        self.session.add(invitation)
        await self.session.commit()
        await self.session.refresh(invitation)

        # Notify the invited user in-app if they already have an account.
        if invited_user is not None:
            organization = await self.session.get(
                Organization,
                organization_id,
            )
            organization_name = (
                organization.name
                if organization is not None
                else "an organization"
            )

            notify_organization_invitation.delay(
                user_id=str(invited_user.id),
                inviter_name=current_user.full_name,
                organization_name=organization_name,
                token=invitation.token,
            )

        return invitation

    async def accept_invitation(
        self,
        *,
        token: str,
        current_user: User,
    ) -> OrgMember:
        statement = select(Invitation).where(Invitation.token == token).with_for_update()

        result = await self.session.execute(statement)
        invitation = result.scalar_one_or_none()

        if invitation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        if invitation.status == InvitationStatus.REVOKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation has been revoked",
            )

        if invitation.status == InvitationStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation has already been accepted",
            )

        if invitation.status == InvitationStatus.EXPIRED:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Invitation has expired",
            )

        now = datetime.now(UTC)

        if invitation.expires_at <= now:
            invitation.status = InvitationStatus.EXPIRED
            await self.session.commit()

            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Invitation has expired",
            )

        invitation_email = invitation.email.strip().lower()
        current_user_email = current_user.email.strip().lower()

        if invitation_email != current_user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation belongs to another user",
            )

        membership = await self.organizations.get_member(
            invitation.organization_id,
            current_user.id,
        )

        if membership is None:
            membership = await self.organizations.add_member(
                organization_id=invitation.organization_id,
                user_id=current_user.id,
                role=invitation.role,
            )

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = now

        await self.session.commit()
        await self.session.refresh(membership)

        return membership

    async def revoke_invitation(
        self,
        *,
        invitation_id: uuid.UUID,
        current_user: User,
    ) -> None:
        invitation = await self.session.get(
            Invitation,
            invitation_id,
        )

        if invitation is None:
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

        if invitation.status == InvitationStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An accepted invitation cannot be revoked",
            )

        if invitation.status == InvitationStatus.REVOKED:
            return

        invitation.status = InvitationStatus.REVOKED

        await self.session.commit()
