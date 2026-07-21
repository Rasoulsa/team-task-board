from __future__ import annotations

import uuid

from app.core.pagination import CursorPage, decode_cursor, encode_cursor
from app.models.activity import ActivityLog
from app.repositories.activity import ActivityRepository
from app.schemas.activity import ActivityRead


class ActivityService:
    def __init__(self, repository: ActivityRepository) -> None:
        self.repository = repository

    # --- Used by CardService (Day 4+) — keep working ---
    async def record(
        self,
        *,
        board_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
        meta: dict | None = None,
    ) -> ActivityLog:
        log = ActivityLog(
            board_id=board_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            meta=meta or {},
        )
        return await self.repository.create(log)

    # --- Legacy simple list (kept if referenced elsewhere) ---
    async def list_board_activity(
        self,
        board_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[ActivityLog]:
        return await self.repository.list_by_board(board_id, limit=limit)

    # --- Day 8: cursor-paginated feed ---
    async def board_feed(
        self,
        *,
        board_id: uuid.UUID,
        limit: int,
        cursor: str | None,
    ) -> CursorPage[ActivityRead]:
        decoded = None
        if cursor is not None:
            decoded = decode_cursor(cursor)  # route catches ValueError -> 400

        rows = await self.repository.list_for_board(
            board_id=board_id,
            limit=limit,
            cursor=decoded,
        )

        has_next = len(rows) > limit
        page_rows = rows[:limit]

        next_cursor = None
        if has_next and page_rows:
            last = page_rows[-1]
            next_cursor = encode_cursor(created_at=last.created_at, item_id=str(last.id))

        items = [
            ActivityRead(
                id=r.id,
                board_id=r.board_id,
                actor_id=r.actor_id,
                actor_name=(r.actor.full_name if r.actor is not None else None),
                action=r.action,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                meta=r.meta,
                created_at=r.created_at,
            )
            for r in page_rows
        ]
        return CursorPage[ActivityRead](items=items, next_cursor=next_cursor)
