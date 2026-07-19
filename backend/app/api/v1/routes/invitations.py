import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.invitation import (
    InvitationAcceptResponse,
    InvitationCreate,
    InvitationRead,
    InvitationRevokeResponse,
)
from app.services.invitations import InvitationService

router = APIRouter(tags=["invitations"])


@router.get(
    "/organizations/{organization_id}/invitations",
    response_model=list[InvitationRead],
)
async def list_invitations(
    organization_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InvitationRead]:
    service = InvitationService(session)

    invitations = await service.list_invitations(
        organization_id=organization_id,
        current_user=current_user,
    )

    return [InvitationRead.model_validate(invitation) for invitation in invitations]


@router.post(
    "/organizations/{organization_id}/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    organization_id: uuid.UUID,
    payload: InvitationCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvitationRead:
    service = InvitationService(session)

    invitation = await service.create_invitation(
        organization_id=organization_id,
        email=str(payload.email),
        role=payload.role,
        current_user=current_user,
    )

    return InvitationRead.model_validate(invitation)


@router.post(
    "/invitations/{token}/accept",
    response_model=InvitationAcceptResponse,
)
async def accept_invitation(
    token: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvitationAcceptResponse:
    service = InvitationService(session)

    membership = await service.accept_invitation(
        token=token,
        current_user=current_user,
    )

    return InvitationAcceptResponse.model_validate(membership)


@router.post(
    "/invitations/{invitation_id}/revoke",
    response_model=InvitationRevokeResponse,
)
async def revoke_invitation(
    invitation_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvitationRevokeResponse:
    service = InvitationService(session)

    await service.revoke_invitation(
        invitation_id=invitation_id,
        current_user=current_user,
    )

    return InvitationRevokeResponse(
        message="Invitation revoked",
    )
