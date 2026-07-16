from __future__ import annotations

import uuid
from typing import Any

import pytest
from sqlalchemy import func, select

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.worker.db import get_sync_session
from app.worker.tasks import (
    _create_notification_once,
    _due_date_deduplication_key,
)


@pytest.mark.asyncio
async def test_due_date_notification_is_created_only_once(
    authenticated_user: dict[str, Any],
) -> None:
    user_id = uuid.UUID(str(authenticated_user["user_id"]))
    card_id = uuid.uuid4()
    due_date = "2026-07-17T10:00:00+00:00"

    key = _due_date_deduplication_key(
        user_id=str(user_id),
        card_id=str(card_id),
        due_date=due_date,
    )

    with get_sync_session() as sync_session:
        first = _create_notification_once(
            sync_session,
            user_id=user_id,
            notif_type=NotificationType.DUE_DATE_REMINDER,
            title="Card due soon",
            body="First attempt",
            board_id=None,
            card_id=None,
            deduplication_key=key,
        )
        sync_session.commit()

        second = _create_notification_once(
            sync_session,
            user_id=user_id,
            notif_type=NotificationType.DUE_DATE_REMINDER,
            title="Card due soon",
            body="Second attempt",
            board_id=None,
            card_id=None,
            deduplication_key=key,
        )
        sync_session.commit()

        notification_count = sync_session.scalar(
            select(func.count(Notification.id)).where(
                Notification.deduplication_key == key,
            )
        )

    assert first is not None
    assert second is None
    assert notification_count == 1
