from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_db,
    get_notification_service,
)
from app.models.user import User
from app.schemas.notification import NotificationRead, UnreadCount
from app.services.notifications import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> list[NotificationRead]:
    notifications = await service.list(
        user.id,
        limit=limit,
        offset=offset,
    )

    return [NotificationRead.model_validate(notification) for notification in notifications]


@router.get("/unread-count", response_model=UnreadCount)
async def unread_count(
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> UnreadCount:
    count = await service.unread_count(user.id)
    return UnreadCount(unread_count=count)


@router.post(
    "/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_all_read(
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
    session: AsyncSession = Depends(get_db),
) -> None:
    await service.mark_all_read(user.id)
    await session.commit()


@router.post(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
    session: AsyncSession = Depends(get_db),
) -> None:
    await service.mark_read(user.id, notification_id)
    await session.commit()
