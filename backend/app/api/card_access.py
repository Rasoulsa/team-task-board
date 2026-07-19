from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.board_access import get_board_and_org_for_card
from app.api.rbac import get_membership, role_allows
from app.models.card import CardAssignee
from app.models.enums import OrganizationRole
from app.models.user import User


async def _is_assignee(
    session: AsyncSession,
    *,
    card_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    result = await session.execute(
        select(CardAssignee).where(
            CardAssignee.card_id == card_id,
            CardAssignee.user_id == user_id,
        ),
    )
    return result.scalar_one_or_none() is not None


async def require_card_read_access(
    session: AsyncSession,
    *,
    card_id: uuid.UUID,
    current_user: User,
) -> tuple[uuid.UUID, uuid.UUID, OrganizationRole]:
    """Return (board_id, org_id, role).

    - VIEWER and above: may read any card in the org.
    - GUEST: may read a card only if assigned to it.
    """
    board_id, org_id = await get_board_and_org_for_card(session, card_id)

    membership = await get_membership(
        session=session,
        organization_id=org_id,
        user_id=current_user.id,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this card",
        )

    if role_allows(membership.role, OrganizationRole.VIEWER):
        return board_id, org_id, membership.role

    if membership.role == OrganizationRole.GUEST and await _is_assignee(
        session,
        card_id=card_id,
        user_id=current_user.id,
    ):
        return board_id, org_id, membership.role

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this card",
    )
