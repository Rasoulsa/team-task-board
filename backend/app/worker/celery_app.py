from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "team_task_board",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

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

# Celery Beat schedule: check for due cards periodically.
celery_app.conf.beat_schedule = {
    "scan-due-cards-every-15-min": {
        "task": "app.worker.tasks.scan_due_cards",
        "schedule": 60 * 15,  # every 15 minutes
    },
}
