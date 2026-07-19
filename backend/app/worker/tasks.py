from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from celery import shared_task
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.card import Card
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.worker.celery_app import celery_app  # noqa: F401  (ensures set_default() runs)
from app.worker.db import get_sync_session
from app.worker.email import send_email
from app.ws.events import EventType
from app.ws.publisher import publish_user_event

logger = structlog.get_logger(__name__)


def _create_notification(
    session: Session,
    *,
    user_id: uuid.UUID,
    notif_type: NotificationType,
    title: str,
    body: str,
    board_id: uuid.UUID | None = None,
    card_id: uuid.UUID | None = None,
) -> tuple[Notification, int]:
    """Persist a notification and return its resulting unread count."""
    notification = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        body=body,
        board_id=board_id,
        card_id=card_id,
    )
    session.add(notification)
    session.flush()

    unread_count = session.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        ),
    )

    return notification, int(unread_count or 0)


def _notification_payload(
    notification: Notification,
    *,
    unread_count: int,
) -> dict[str, Any]:
    """Build the WebSocket payload for a freshly created notification.

    Field names intentionally match `NotificationRead` so the frontend
    can render a pushed notification without an extra REST round trip.
    """
    return {
        "id": str(notification.id),
        "type": str(notification.type),
        "title": notification.title,
        "body": notification.body,
        "board_id": (str(notification.board_id) if notification.board_id is not None else None),
        "card_id": (str(notification.card_id) if notification.card_id is not None else None),
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
        "unread_count": unread_count,
    }


def _publish_notification(
    notification: Notification,
    *,
    unread_count: int,
) -> None:
    """Best-effort live publication after the database commit."""
    try:
        publish_user_event(
            str(notification.user_id),
            event_type=EventType.NOTIFICATION_CREATED,
            payload=_notification_payload(
                notification,
                unread_count=unread_count,
            ),
        )
    except Exception:
        logger.exception(
            "notification.publish_failed",
            user_id=str(notification.user_id),
            notification_id=str(notification.id),
        )


def _create_notification_once(
    session: Session,
    *,
    user_id: uuid.UUID,
    notif_type: NotificationType,
    title: str,
    body: str,
    deduplication_key: str,
    board_id: uuid.UUID | None = None,
    card_id: uuid.UUID | None = None,
) -> tuple[Notification, int] | None:
    statement = (
        pg_insert(Notification)
        .values(
            id=uuid.uuid4(),
            user_id=user_id,
            type=notif_type,
            title=title,
            body=body,
            board_id=board_id,
            card_id=card_id,
            is_read=False,
            deduplication_key=deduplication_key,
        )
        .on_conflict_do_nothing(
            index_elements=[Notification.deduplication_key],
        )
        .returning(Notification)
    )

    notification = session.execute(statement).scalar_one_or_none()

    if notification is None:
        return None

    unread_count = session.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    )

    return notification, int(unread_count or 0)


def _due_date_deduplication_key(
    *,
    user_id: str,
    card_id: str,
    due_date: str,
) -> str:
    parsed_due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))

    if parsed_due_date.tzinfo is None:
        parsed_due_date = parsed_due_date.replace(tzinfo=UTC)

    canonical_due_date = parsed_due_date.astimezone(UTC).isoformat()

    return f"due-date:{user_id}:{card_id}:{canonical_due_date}"


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def notify_card_assigned(
    *,
    user_id: str,
    assigner_name: str,
    card_id: str,
    card_title: str,
    board_id: str,
) -> None:
    with get_sync_session() as session:
        user = session.get(User, uuid.UUID(user_id))

        if user is None:
            logger.warning("notify.user_missing", user_id=user_id)
            return

        notification, unread_count = _create_notification(
            session,
            user_id=user.id,
            notif_type=NotificationType.CARD_ASSIGNED,
            title="You were assigned a card",
            body=f'{assigner_name} assigned you to "{card_title}".',
            board_id=uuid.UUID(board_id),
            card_id=uuid.UUID(card_id),
        )

        # Snapshot fields needed after commit.
        recipient_email = user.email

        session.commit()

        _publish_notification(
            notification,
            unread_count=unread_count,
        )

        try:
            send_email(
                to=recipient_email,
                subject="You were assigned a card",
                body=f'{assigner_name} assigned you to "{card_title}".',
            )
        except Exception:
            logger.exception(
                "notification.email_failed",
                user_id=user_id,
                notification_id=str(notification.id),
            )


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def notify_card_mentioned(
    *,
    user_id: str,
    author_name: str,
    card_id: str,
    card_title: str,
    board_id: str,
) -> None:
    with get_sync_session() as session:
        user = session.get(User, uuid.UUID(user_id))

        if user is None:
            logger.warning("notify.user_missing", user_id=user_id)
            return

        notification, unread_count = _create_notification(
            session,
            user_id=user.id,
            notif_type=NotificationType.CARD_MENTIONED,
            title="You were mentioned",
            body=f'{author_name} mentioned you on "{card_title}".',
            board_id=uuid.UUID(board_id),
            card_id=uuid.UUID(card_id),
        )

        recipient_email = user.email

        session.commit()

        _publish_notification(
            notification,
            unread_count=unread_count,
        )

        try:
            send_email(
                to=recipient_email,
                subject="You were mentioned in a comment",
                body=f'{author_name} mentioned you on "{card_title}".',
            )
        except Exception:
            logger.exception(
                "notification.email_failed",
                user_id=user_id,
                notification_id=str(notification.id),
            )


@shared_task
def scan_due_cards() -> int:
    """Beat task: find cards due within the reminder window and notify assignees.

    Returns the number of reminder tasks enqueued (useful for tests/logs).
    """
    now = datetime.now(UTC)
    window_end = now + timedelta(hours=settings.DUE_REMINDER_HOURS)

    enqueued = 0
    with get_sync_session() as session:
        due_cards = session.scalars(
            select(Card).where(
                Card.due_date.is_not(None),
                Card.due_date >= now,
                Card.due_date <= window_end,
                Card.is_deleted.is_(False),
            )
        ).all()

        for card in due_cards:
            due_date = card.due_date

            if due_date is None:
                continue

            for assignee in card.assignees:
                notify_due_date.delay(
                    user_id=str(assignee.id),
                    card_id=str(card.id),
                    card_title=card.title,
                    board_id=str(card.column.board_id),
                    due_date=due_date.isoformat(),
                )
                enqueued += 1

    logger.info("scan_due_cards.done", enqueued=enqueued)
    return enqueued


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def notify_due_date(
    *,
    user_id: str,
    card_id: str,
    card_title: str,
    board_id: str,
    due_date: str,
) -> None:
    with get_sync_session() as session:
        user = session.get(User, uuid.UUID(user_id))

        if user is None:
            logger.warning("notify.user_missing", user_id=user_id)
            return

        title = "Card due soon"
        body = f'"{card_title}" is due at {due_date}.'

        deduplication_key = _due_date_deduplication_key(
            user_id=user_id,
            card_id=card_id,
            due_date=due_date,
        )

        result = _create_notification_once(
            session,
            user_id=user.id,
            notif_type=NotificationType.DUE_DATE_REMINDER,
            title=title,
            body=body,
            board_id=uuid.UUID(board_id),
            card_id=uuid.UUID(card_id),
            deduplication_key=deduplication_key,
        )

        if result is None:
            logger.info(
                "notification.due_date_duplicate_skipped",
                user_id=user_id,
                card_id=card_id,
                due_date=due_date,
            )
            return

        notification, unread_count = result
        recipient_email = user.email

        session.commit()

        _publish_notification(
            notification,
            unread_count=unread_count,
        )

        try:
            send_email(
                to=recipient_email,
                subject=title,
                body=body,
            )
        except Exception:
            logger.exception(
                "notification.email_failed",
                user_id=user_id,
                notification_id=str(notification.id),
            )


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def notify_organization_invitation(
    *,
    user_id: str,
    inviter_name: str,
    organization_name: str,
    token: str,
) -> None:
    with get_sync_session() as session:
        user = session.get(User, uuid.UUID(user_id))

        if user is None:
            logger.warning("notify.user_missing", user_id=user_id)
            return

        title = "You were invited to an organization"
        body = (
            f'{inviter_name} invited you to join "{organization_name}". '
            f"Open your invitations to accept."
        )

        notification, unread_count = _create_notification(
            session,
            user_id=user.id,
            notif_type=NotificationType.ORGANIZATION_INVITATION,
            title=title,
            body=body,
        )

        recipient_email = user.email
        session.commit()

        _publish_notification(notification, unread_count=unread_count)

        try:
            send_email(
                to=recipient_email,
                subject=title,
                body=f"{body}\n\nInvitation token: {token}",
            )
        except Exception:
            logger.exception(
                "notification.email_failed",
                user_id=user_id,
                notification_id=str(notification.id),
            )
