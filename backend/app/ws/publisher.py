from __future__ import annotations

from functools import lru_cache
from typing import Any

from redis import Redis

from app.core.config import settings
from app.ws.events import EventType, UserRealtimeEvent


@lru_cache
def _get_redis_client() -> Redis:
    """Return a process-local synchronous Redis client.

    Celery worker processes initialize this lazily when they publish their
    first event.
    """
    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


def publish_user_event(
    user_id: str,
    *,
    event_type: EventType,
    payload: dict[str, Any],
) -> None:
    """Publish an event to one user's private WebSocket channel."""
    event = UserRealtimeEvent(
        type=event_type,
        user_id=user_id,
        payload=payload,
    )

    client = _get_redis_client()
    client.publish(
        UserRealtimeEvent.channel_for(user_id),
        event.to_json(),
    )
