from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.board_access import get_org_for_board
from app.api.deps import get_current_user, get_db_session
from app.api.rbac import require_org_role
from app.models.enums import OrganizationRole
from app.models.user import User
from app.schemas.stats import BoardStats
from app.services.stats import StatsService

router = APIRouter(tags=["stats"])


@router.get("/boards/{board_id}/stats", response_model=BoardStats)
async def get_board_stats(
    board_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> BoardStats:
    org_id = await get_org_for_board(session, board_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.VIEWER,
    )

    service = StatsService(session)
    return await service.board_stats(board_id=board_id, organization_id=org_id)
