from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.routes.cards import _publish
from app.ws.events import EventType, RealtimeEvent


@pytest.mark.asyncio
async def test_publish_sends_all_collected_events() -> None:
    event = RealtimeEvent(
        type=EventType.CARD_MOVED,
        board_id=str(uuid.uuid4()),
        actor_id=str(uuid.uuid4()),
        payload={
            "id": str(uuid.uuid4()),
            "column_id": str(uuid.uuid4()),
            "rank": "m",
        },
    )

    service = MagicMock()
    service.collect_events.return_value = [event]

    event_bridge = MagicMock()
    event_bridge.publish = AsyncMock()

    await _publish(event_bridge, service)

    service.collect_events.assert_called_once_with()
    event_bridge.publish.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_publish_does_nothing_when_no_events_exist() -> None:
    service = MagicMock()
    service.collect_events.return_value = []

    event_bridge = MagicMock()
    event_bridge.publish = AsyncMock()

    await _publish(event_bridge, service)

    service.collect_events.assert_called_once_with()
    event_bridge.publish.assert_not_awaited()
