from __future__ import annotations

from celery import Celery

from app.core.config import settings

_is_testing = settings.ENV == "testing"

celery_app = Celery(
    "team_task_board",
    broker=settings.CELERY_BROKER_URL if not _is_testing else "memory://",
    backend=settings.CELERY_RESULT_BACKEND if not _is_testing else None,
    include=["app.worker.tasks"],
)

# Make this the current/default Celery app so `@shared_task`-decorated
# tasks bind to it and inherit its configuration (e.g. eager mode in tests).
celery_app.set_default()

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_time_limit=60,
    task_soft_time_limit=50,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=5,
    task_max_retries=3,
    timezone="UTC",
    enable_utc=True,
)

if _is_testing:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_connection_retry_on_startup=False,
    )

celery_app.conf.beat_schedule = {
    "scan-due-cards-every-15-min": {
        "task": "app.worker.tasks.scan_due_cards",
        "schedule": 60 * 15,
    },
}
