from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.board_access import get_board_and_org_for_card
from app.api.deps import get_current_user, get_db_session
from app.api.rbac import require_org_role
from app.models.enums import OrganizationRole
from app.models.user import User
from app.repositories.activity import ActivityRepository
from app.repositories.comments import CommentRepository
from app.schemas.comment import CommentCreate, CommentRead
from app.services.activity import ActivityService
from app.services.comments import CommentService

router = APIRouter(tags=["comments"])


def build_comment_service(session: AsyncSession) -> CommentService:
    activity_service = ActivityService(ActivityRepository(session))
    return CommentService(
        session=session,
        repository=CommentRepository(session),
        activity_service=activity_service,
    )


@router.get(
    "/cards/{card_id}/comments",
    response_model=list[CommentRead],
)
async def list_comments(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[CommentRead]:
    _, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.VIEWER,
    )

    service = build_comment_service(session)
    comments = await service.list_comments(card_id)
    return [CommentRead.model_validate(comment) for comment in comments]


@router.post(
    "/cards/{card_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    card_id: uuid.UUID,
    payload: CommentCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CommentRead:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )

    service = build_comment_service(session)
    comment = await service.create_comment(
        board_id=board_id,
        card_id=card_id,
        author_id=current_user.id,
        body=payload.body,
    )
    await session.commit()
    return CommentRead.model_validate(comment)
