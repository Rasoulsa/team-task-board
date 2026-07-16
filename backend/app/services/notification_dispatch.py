from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class CeleryTaskLike(Protocol):
    """Minimal protocol for a Celery task: we only ever call `.delay()`."""

    def delay(self, *args: Any, **kwargs: Any) -> Any: ...


@dataclass(frozen=True)
class PendingNotificationTask:
    """A deferred Celery task enqueue, queued by a service during a
    transaction and only `.delay()`'d by the router after commit."""

    task: CeleryTaskLike
    kwargs: dict[str, Any]


class HasNotificationTasks(Protocol):
    def collect_notification_tasks(self) -> list[PendingNotificationTask]: ...


def enqueue_notifications(service: HasNotificationTasks) -> None:
    """Enqueue any notification tasks queued by a service.

    Call this only after `session.commit()` has succeeded, mirroring
    how realtime events are published post-commit.
    """
    for pending in service.collect_notification_tasks():
        pending.task.delay(**pending.kwargs)
