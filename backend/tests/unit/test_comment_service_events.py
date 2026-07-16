from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.comments import CommentService
from app.ws.events import EventType


@pytest.mark.asyncio
async def test_create_comment_queues_comment_created_event(
    mocker: MockerFixture,
) -> None:
    board_id = uuid.uuid4()
    card_id = uuid.uuid4()
    author_id = uuid.uuid4()
    comment_id = uuid.uuid4()
    mentioned_user_id = uuid.uuid4()

    session = MagicMock(spec=AsyncSession)

    repository = MagicMock()
    repository.session = session
    repository.create = AsyncMock(
        return_value=SimpleNamespace(id=comment_id),
    )
    repository.add_mention = AsyncMock()

    activity_service = MagicMock()
    activity_service.record = AsyncMock()

    service = CommentService(
        session=session,
        repository=repository,
        activity_service=activity_service,
    )

    reloaded_comment = SimpleNamespace(
        id=comment_id,
        card_id=card_id,
        author_id=author_id,
        body="Hello @member",
        mentions=[],
    )

    mocker.patch.object(
        service,
        "_resolve_mentions",
        new=AsyncMock(return_value=[mentioned_user_id]),
    )
    mocker.patch.object(
        service,
        "_reload",
        new=AsyncMock(return_value=reloaded_comment),
    )

    result = await service.create_comment(
        board_id=board_id,
        card_id=card_id,
        author_id=author_id,
        body="Hello @member",
        author_name="Test User",
    )

    assert result is reloaded_comment

    activity_service.record.assert_awaited_once_with(
        board_id=board_id,
        actor_id=author_id,
        action="comment.created",
        entity_type="comment",
        entity_id=comment_id,
        meta={"mentions": [str(mentioned_user_id)]},
    )

    events = service.collect_events()

    assert len(events) == 1

    event = events[0]

    assert event.type == EventType.COMMENT_CREATED
    assert event.board_id == str(board_id)
    assert event.actor_id == str(author_id)
    assert event.payload == {
        "id": str(comment_id),
        "card_id": str(card_id),
        "mentions": [str(mentioned_user_id)],
    }


@pytest.mark.asyncio
async def test_collect_events_clears_comment_service_queue(
    mocker: MockerFixture,
) -> None:
    board_id = uuid.uuid4()
    card_id = uuid.uuid4()
    author_id = uuid.uuid4()
    comment_id = uuid.uuid4()

    session = MagicMock(spec=AsyncSession)

    repository = MagicMock()
    repository.session = session
    repository.create = AsyncMock(
        return_value=SimpleNamespace(id=comment_id),
    )
    repository.add_mention = AsyncMock()

    activity_service = MagicMock()
    activity_service.record = AsyncMock()

    service = CommentService(
        session=session,
        repository=repository,
        activity_service=activity_service,
    )

    mocker.patch.object(
        service,
        "_resolve_mentions",
        new=AsyncMock(return_value=[]),
    )
    mocker.patch.object(
        service,
        "_reload",
        new=AsyncMock(
            return_value=SimpleNamespace(
                id=comment_id,
                card_id=card_id,
                author_id=author_id,
                body="No mentions",
                mentions=[],
            ),
        ),
    )

    await service.create_comment(
        board_id=board_id,
        card_id=card_id,
        author_id=author_id,
        body="No mentions",
        author_name="Test User",
    )

    first_collection = service.collect_events()
    second_collection = service.collect_events()

    assert len(first_collection) == 1
    assert second_collection == []
