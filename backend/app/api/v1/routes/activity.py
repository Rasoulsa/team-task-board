from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.board_access import get_org_for_board
from app.api.deps import get_current_user, get_db_session
from app.api.rbac import require_org_role
from app.models.enums import OrganizationRole
from app.models.user import User
from app.repositories.activity import ActivityRepository
from app.schemas.activity import ActivityLogRead
from app.services.activity import ActivityService

router = APIRouter(tags=["activity"])


@router.get(
    "/boards/{board_id}/activity",
    response_model=list[ActivityLogRead],
)
async def list_board_activity(
    board_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[ActivityLogRead]:
    org_id = await get_org_for_board(session, board_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.VIEWER,
    )

    service = ActivityService(ActivityRepository(session))
    logs = await service.list_board_activity(board_id, limit=limit)
    return [ActivityLogRead.model_validate(log) for log in logs]
