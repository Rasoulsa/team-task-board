from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.cards import CardService
from app.ws.events import EventType


@pytest.mark.asyncio
async def test_move_card_queues_card_moved_event() -> None:
    board_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    card_id = uuid.uuid4()
    source_column_id = uuid.uuid4()
    target_column_id = uuid.uuid4()

    repository = MagicMock()
    repository.session.flush = AsyncMock()

    activity_service = MagicMock()
    activity_service.record = AsyncMock()

    service = CardService(
        repository=repository,
        activity_service=activity_service,
    )

    card = SimpleNamespace(
        id=card_id,
        column_id=source_column_id,
        rank="m",
    )

    service.get_card = AsyncMock(return_value=card)

    payload = SimpleNamespace(
        target_column_id=target_column_id,
        previous_card_id=None,
        next_card_id=None,
    )

    moved_card = await service.move_card(
        board_id=board_id,
        card_id=card_id,
        actor_id=actor_id,
        payload=payload,
    )

    assert moved_card.id == card_id
    assert moved_card.column_id == target_column_id

    repository.session.flush.assert_awaited_once()

    activity_service.record.assert_awaited_once_with(
        board_id=board_id,
        actor_id=actor_id,
        action="card.moved",
        entity_type="card",
        entity_id=card_id,
        meta={"column_id": str(target_column_id)},
    )

    events = service.collect_events()

    assert len(events) == 1

    event = events[0]

    assert event.type == EventType.CARD_MOVED
    assert event.board_id == str(board_id)
    assert event.actor_id == str(actor_id)
    assert event.payload["id"] == str(card_id)
    assert event.payload["column_id"] == str(target_column_id)
    assert event.payload["rank"] == moved_card.rank


@pytest.mark.asyncio
async def test_collect_events_clears_card_service_queue() -> None:
    board_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    card_id = uuid.uuid4()
    column_id = uuid.uuid4()

    repository = MagicMock()
    repository.session.flush = AsyncMock()

    activity_service = MagicMock()
    activity_service.record = AsyncMock()

    service = CardService(
        repository=repository,
        activity_service=activity_service,
    )

    card = SimpleNamespace(
        id=card_id,
        column_id=column_id,
        rank="m",
    )

    service.get_card = AsyncMock(return_value=card)

    payload = SimpleNamespace(
        target_column_id=column_id,
        previous_card_id=None,
        next_card_id=None,
    )

    await service.move_card(
        board_id=board_id,
        card_id=card_id,
        actor_id=actor_id,
        payload=payload,
    )

    first_collection = service.collect_events()
    second_collection = service.collect_events()

    assert len(first_collection) == 1
    assert second_collection == []
