# Notifications & Celery

## Goal
Deliver assignment, mention, and due-date notifications asynchronously,
persist them, and push live unread-count updates to the notification bell.

## Flow
Trigger (assign / mention / due-soon) → enqueue Celery task (Redis broker)
→ worker creates Notification row, sends email, publishes to
`user:{id}:events` → frontend updates bell badge and panel live.

## Key decisions
- **User-scoped channel** (`user:{id}:events`) separate from Day 6's
  board channel, so the bell updates on every page, via a dedicated
  `/ws/notifications` socket.
- **Sync DB session in workers** (`app/worker/db.py`) to avoid mixing the
  async engine into Celery processes.
- **Enqueue after commit**, and only for *newly* assigned/mentioned users,
  so a re-save never re-notifies everyone and rolled-back changes never
  enqueue.
- **Retry policy**: `autoretry_for`, exponential backoff + jitter,
  `max_retries=3`. Email failures retry; a failed live-publish is
  best-effort and never rolls back the persisted notification.
- **Due-date reminders** via Celery Beat (`scan_due_cards`, every 15 min),
  reminder window configurable (`DUE_REMINDER_HOURS`).

## Endpoints
GET  /api/v1/notifications
GET  /api/v1/notifications/unread-count
POST /api/v1/notifications/{id}/read
POST /api/v1/notifications/read-all
WS   /api/v1/ws/notifications?token=...