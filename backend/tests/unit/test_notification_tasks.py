# tests/unit/test_notification_tasks.py

from __future__ import annotations

import uuid
from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.models.enums import NotificationType
from app.models.notification import Notification
from app.models.user import User
from app.worker.tasks import (
    _due_date_deduplication_key,
    _notification_payload,
    _publish_notification,
    notify_card_assigned,
    notify_card_mentioned,
    notify_due_date,
    scan_due_cards,
)
from app.ws.events import EventType


def make_notification(
    *,
    user_id: uuid.UUID | None = None,
    notification_type: NotificationType = NotificationType.CARD_ASSIGNED,
    board_id: uuid.UUID | None = None,
    card_id: uuid.UUID | None = None,
) -> Notification:
    return Notification(
        id=uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        type=notification_type,
        title="Notification title",
        body="Notification body",
        board_id=board_id if board_id is not None else uuid.uuid4(),
        card_id=card_id if card_id is not None else uuid.uuid4(),
        is_read=False,
        created_at=datetime.now(UTC),
    )


def test_notification_payload_matches_api_shape() -> None:
    notification = make_notification()

    payload = _notification_payload(
        notification,
        unread_count=3,
    )

    assert payload == {
        "id": str(notification.id),
        "type": str(notification.type),
        "title": notification.title,
        "body": notification.body,
        "board_id": str(notification.board_id),
        "card_id": str(notification.card_id),
        "is_read": False,
        "created_at": notification.created_at.isoformat(),
        "unread_count": 3,
    }


def test_notification_payload_allows_missing_deep_link_context() -> None:
    notification = Notification(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        type=NotificationType.CARD_ASSIGNED,
        title="Notification title",
        body="Notification body",
        board_id=None,
        card_id=None,
        is_read=False,
        created_at=datetime.now(UTC),
    )

    payload = _notification_payload(
        notification,
        unread_count=1,
    )

    assert payload["board_id"] is None
    assert payload["card_id"] is None


def test_notify_card_assigned_creates_and_publishes_notification() -> None:
    user_id = uuid.uuid4()
    board_id = uuid.uuid4()
    card_id = uuid.uuid4()

    user = SimpleNamespace(
        id=user_id,
        email="assigned@example.com",
    )
    notification = make_notification(
        user_id=user_id,
        notification_type=NotificationType.CARD_ASSIGNED,
    )

    session = MagicMock()
    session.get.return_value = user

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks._create_notification",
            return_value=(notification, 2),
        ) as create_notification,
        patch(
            "app.worker.tasks._publish_notification",
        ) as publish_notification,
        patch(
            "app.worker.tasks.send_email",
        ) as send_email,
    ):
        notify_card_assigned.run(
            user_id=str(user_id),
            assigner_name="Alice",
            card_id=str(card_id),
            card_title="Implement notifications",
            board_id=str(board_id),
        )

    session.get.assert_called_once_with(User, user_id)

    create_notification.assert_called_once_with(
        session,
        user_id=user_id,
        notif_type=NotificationType.CARD_ASSIGNED,
        title="You were assigned a card",
        body='Alice assigned you to "Implement notifications".',
        board_id=board_id,
        card_id=card_id,
    )
    session.commit.assert_called_once_with()

    publish_notification.assert_called_once_with(
        notification,
        unread_count=2,
    )
    send_email.assert_called_once_with(
        to="assigned@example.com",
        subject="You were assigned a card",
        body='Alice assigned you to "Implement notifications".',
    )


def test_notify_card_assigned_returns_when_user_does_not_exist() -> None:
    user_id = uuid.uuid4()

    session = MagicMock()
    session.get.return_value = None

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks._create_notification",
        ) as create_notification,
        patch(
            "app.worker.tasks._publish_notification",
        ) as publish_notification,
        patch(
            "app.worker.tasks.send_email",
        ) as send_email,
    ):
        result = notify_card_assigned.run(
            user_id=str(user_id),
            assigner_name="Alice",
            card_id=str(uuid.uuid4()),
            card_title="Missing-user test",
            board_id=str(uuid.uuid4()),
        )

    assert result is None
    create_notification.assert_not_called()
    session.commit.assert_not_called()
    publish_notification.assert_not_called()
    send_email.assert_not_called()


def test_notify_card_assigned_email_failure_does_not_fail_task() -> None:
    user_id = uuid.uuid4()

    user = SimpleNamespace(
        id=user_id,
        email="assigned@example.com",
    )
    notification = make_notification(
        user_id=user_id,
        notification_type=NotificationType.CARD_ASSIGNED,
    )

    session = MagicMock()
    session.get.return_value = user

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks._create_notification",
            return_value=(notification, 1),
        ),
        patch(
            "app.worker.tasks._publish_notification",
        ),
        patch(
            "app.worker.tasks.send_email",
            side_effect=RuntimeError("SMTP unavailable"),
        ),
    ):
        result = notify_card_assigned.run(
            user_id=str(user_id),
            assigner_name="Alice",
            card_id=str(uuid.uuid4()),
            card_title="Email failure test",
            board_id=str(uuid.uuid4()),
        )

    assert result is None
    session.commit.assert_called_once_with()


def test_notify_card_mentioned_creates_and_publishes_notification() -> None:
    user_id = uuid.uuid4()
    board_id = uuid.uuid4()
    card_id = uuid.uuid4()

    user = SimpleNamespace(
        id=user_id,
        email="mentioned@example.com",
    )
    notification = make_notification(
        user_id=user_id,
        notification_type=NotificationType.CARD_MENTIONED,
    )

    session = MagicMock()
    session.get.return_value = user

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks._create_notification",
            return_value=(notification, 4),
        ) as create_notification,
        patch(
            "app.worker.tasks._publish_notification",
        ) as publish_notification,
        patch(
            "app.worker.tasks.send_email",
        ) as send_email,
    ):
        notify_card_mentioned.run(
            user_id=str(user_id),
            author_name="Bob",
            card_id=str(card_id),
            card_title="Review pull request",
            board_id=str(board_id),
        )

    create_notification.assert_called_once_with(
        session,
        user_id=user_id,
        notif_type=NotificationType.CARD_MENTIONED,
        title="You were mentioned",
        body='Bob mentioned you on "Review pull request".',
        board_id=board_id,
        card_id=card_id,
    )
    session.commit.assert_called_once_with()

    publish_notification.assert_called_once_with(
        notification,
        unread_count=4,
    )
    send_email.assert_called_once_with(
        to="mentioned@example.com",
        subject="You were mentioned in a comment",
        body='Bob mentioned you on "Review pull request".',
    )


def test_notify_due_date_creates_and_publishes_notification() -> None:
    user_id = uuid.uuid4()
    board_id = uuid.uuid4()
    card_id = uuid.uuid4()
    due_date = "2026-07-17T10:00:00+00:00"

    user = SimpleNamespace(
        id=user_id,
        email="due-date@example.com",
    )
    notification = make_notification(
        user_id=user_id,
        notification_type=NotificationType.DUE_DATE_REMINDER,
        board_id=board_id,
        card_id=card_id,
    )

    session = MagicMock()
    session.get.return_value = user

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks._create_notification_once",
            return_value=(notification, 5),
        ) as create_once,
        patch(
            "app.worker.tasks._publish_notification",
        ) as publish_notification,
        patch(
            "app.worker.tasks.send_email",
        ) as send_email,
    ):
        result = notify_due_date.run(
            user_id=str(user_id),
            card_id=str(card_id),
            card_title="Finish notification tests",
            board_id=str(board_id),
            due_date=due_date,
        )

    assert result is None

    session.get.assert_called_once_with(User, user_id)

    expected_key = f"due-date:{user_id}:{card_id}:{due_date}"

    create_once.assert_called_once_with(
        session,
        user_id=user_id,
        notif_type=NotificationType.DUE_DATE_REMINDER,
        title="Card due soon",
        body=f'"Finish notification tests" is due at {due_date}.',
        board_id=board_id,
        card_id=card_id,
        deduplication_key=expected_key,
    )

    session.commit.assert_called_once_with()

    publish_notification.assert_called_once_with(
        notification,
        unread_count=5,
    )

    send_email.assert_called_once_with(
        to="due-date@example.com",
        subject="Card due soon",
        body=f'"Finish notification tests" is due at {due_date}.',
    )


def test_notify_due_date_returns_when_user_does_not_exist() -> None:
    user_id = uuid.uuid4()

    session = MagicMock()
    session.get.return_value = None

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks._create_notification_once",
        ) as create_once,
        patch(
            "app.worker.tasks._publish_notification",
        ) as publish_notification,
        patch(
            "app.worker.tasks.send_email",
        ) as send_email,
    ):
        result = notify_due_date.run(
            user_id=str(user_id),
            card_id=str(uuid.uuid4()),
            card_title="Missing user",
            board_id=str(uuid.uuid4()),
            due_date="2026-07-17T10:00:00+00:00",
        )

    assert result is None
    session.commit.assert_not_called()
    create_once.assert_not_called()
    publish_notification.assert_not_called()
    send_email.assert_not_called()


def test_notify_due_date_email_failure_does_not_undo_notification() -> None:
    user_id = uuid.uuid4()
    board_id = uuid.uuid4()
    card_id = uuid.uuid4()
    due_date = "2026-07-17T10:00:00+00:00"

    user = SimpleNamespace(
        id=user_id,
        email="due-date@example.com",
    )
    notification = make_notification(
        user_id=user_id,
        notification_type=NotificationType.DUE_DATE_REMINDER,
        board_id=board_id,
        card_id=card_id,
    )

    session = MagicMock()
    session.get.return_value = user

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks._create_notification_once",
            return_value=(notification, 1),
        ) as create_once,
        patch(
            "app.worker.tasks._publish_notification",
        ) as publish_notification,
        patch(
            "app.worker.tasks.send_email",
            side_effect=RuntimeError("SMTP unavailable"),
        ) as send_email,
    ):
        result = notify_due_date.run(
            user_id=str(user_id),
            card_id=str(card_id),
            card_title="Email failure test",
            board_id=str(board_id),
            due_date=due_date,
        )

    assert result is None

    create_once.assert_called_once_with(
        session,
        user_id=user_id,
        notif_type=NotificationType.DUE_DATE_REMINDER,
        title="Card due soon",
        body=f'"Email failure test" is due at {due_date}.',
        board_id=board_id,
        card_id=card_id,
        deduplication_key=f"due-date:{user_id}:{card_id}:{due_date}",
    )

    session.commit.assert_called_once_with()

    publish_notification.assert_called_once_with(
        notification,
        unread_count=1,
    )

    send_email.assert_called_once_with(
        to="due-date@example.com",
        subject="Card due soon",
        body=f'"Email failure test" is due at {due_date}.',
    )


def test_scan_due_cards_enqueues_reminder_for_each_assignee() -> None:
    board_id = uuid.uuid4()
    card_id = uuid.uuid4()
    first_user_id = uuid.uuid4()
    second_user_id = uuid.uuid4()
    due_date = datetime.now(UTC) + timedelta(hours=1)

    card = SimpleNamespace(
        id=card_id,
        title="Card due soon",
        due_date=due_date,
        column=SimpleNamespace(board_id=board_id),
        assignees=[
            SimpleNamespace(id=first_user_id),
            SimpleNamespace(id=second_user_id),
        ],
    )

    session = MagicMock()
    session.scalars.return_value.all.return_value = [card]

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks.notify_due_date.delay",
        ) as delay,
    ):
        result = scan_due_cards.run()

    assert result == 2
    assert delay.call_count == 2

    delay.assert_any_call(
        user_id=str(first_user_id),
        card_id=str(card_id),
        card_title="Card due soon",
        board_id=str(board_id),
        due_date=due_date.isoformat(),
    )
    delay.assert_any_call(
        user_id=str(second_user_id),
        card_id=str(card_id),
        card_title="Card due soon",
        board_id=str(board_id),
        due_date=due_date.isoformat(),
    )


def test_scan_due_cards_returns_zero_when_no_cards_are_due() -> None:
    session = MagicMock()
    session.scalars.return_value.all.return_value = []

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks.notify_due_date.delay",
        ) as delay,
    ):
        result = scan_due_cards.run()

    assert result == 0
    delay.assert_not_called()


def test_scan_due_cards_skips_card_without_due_date() -> None:
    card = SimpleNamespace(
        id=uuid.uuid4(),
        title="Card without due date",
        due_date=None,
        column=SimpleNamespace(board_id=uuid.uuid4()),
        assignees=[SimpleNamespace(id=uuid.uuid4())],
    )

    session = MagicMock()
    session.scalars.return_value.all.return_value = [card]

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks.notify_due_date.delay",
        ) as delay,
    ):
        result = scan_due_cards.run()

    assert result == 0
    delay.assert_not_called()


def test_publish_notification_publishes_user_event() -> None:
    notification = make_notification()

    with patch(
        "app.worker.tasks.publish_user_event",
    ) as publish_user_event:
        _publish_notification(notification, unread_count=3)

    publish_user_event.assert_called_once_with(
        str(notification.user_id),
        event_type=EventType.NOTIFICATION_CREATED,
        payload=_notification_payload(
            notification,
            unread_count=3,
        ),
    )


def test_publish_notification_swallows_publication_failure() -> None:
    notification = make_notification()

    with patch(
        "app.worker.tasks.publish_user_event",
        side_effect=RuntimeError("Redis unavailable"),
    ) as publish_user_event:
        _publish_notification(notification, unread_count=2)

    publish_user_event.assert_called_once()


def test_due_date_deduplication_key_normalizes_to_utc() -> None:
    user_id = str(uuid.uuid4())
    card_id = str(uuid.uuid4())

    utc_key = _due_date_deduplication_key(
        user_id=user_id,
        card_id=card_id,
        due_date="2026-07-17T10:00:00+00:00",
    )

    offset_key = _due_date_deduplication_key(
        user_id=user_id,
        card_id=card_id,
        due_date="2026-07-17T13:30:00+03:30",
    )

    assert utc_key == offset_key
    assert utc_key == (f"due-date:{user_id}:{card_id}:2026-07-17T10:00:00+00:00")


def test_notify_due_date_skips_duplicate_notification() -> None:
    user_id = uuid.uuid4()
    card_id = uuid.uuid4()
    board_id = uuid.uuid4()
    due_date = "2026-07-17T10:00:00+00:00"

    user = SimpleNamespace(
        id=user_id,
        email="user@example.com",
    )

    session = MagicMock()
    session.get.return_value = user

    with (
        patch(
            "app.worker.tasks.get_sync_session",
            return_value=nullcontext(session),
        ),
        patch(
            "app.worker.tasks._create_notification_once",
            return_value=None,
        ) as create_once,
        patch(
            "app.worker.tasks._publish_notification",
        ) as publish_notification,
        patch(
            "app.worker.tasks.send_email",
        ) as send_email,
    ):
        result = notify_due_date.run(
            user_id=str(user_id),
            card_id=str(card_id),
            card_title="Finish tests",
            board_id=str(board_id),
            due_date=due_date,
        )

    assert result is None

    session.get.assert_called_once_with(User, user_id)

    create_once.assert_called_once_with(
        session,
        user_id=user_id,
        notif_type=NotificationType.DUE_DATE_REMINDER,
        title="Card due soon",
        body=f'"Finish tests" is due at {due_date}.',
        board_id=board_id,
        card_id=card_id,
        deduplication_key=f"due-date:{user_id}:{card_id}:{due_date}",
    )

    session.commit.assert_not_called()
    publish_notification.assert_not_called()
    send_email.assert_not_called()
