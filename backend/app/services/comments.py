from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.card import Card
from app.models.comment import Comment, CommentMention
from app.models.user import User
from app.repositories.comments import CommentRepository
from app.services.activity import ActivityService
from app.services.notification_dispatch import PendingNotificationTask
from app.worker.tasks import notify_card_mentioned
from app.ws.events import EventType, RealtimeEvent

MENTION_PATTERN = re.compile(r"@([a-zA-Z0-9_.-]+)")


class CommentService:
    def __init__(
        self,
        session: AsyncSession,
        repository: CommentRepository,
        activity_service: ActivityService,
    ) -> None:
        self.session = session
        self.repository = repository
        self.activity_service = activity_service
        self._pending_events: list[RealtimeEvent] = []
        self._pending_notifications: list[PendingNotificationTask] = []

    def _queue_event(self, event: RealtimeEvent) -> None:
        self._pending_events.append(event)

    def collect_events(self) -> list[RealtimeEvent]:
        """Return queued events and clear the buffer.

        Publish these only after the surrounding transaction commits.
        """
        events = self._pending_events
        self._pending_events = []
        return events

    def _queue_notification(self, task: Any, **kwargs: Any) -> None:
        self._pending_notifications.append(
            PendingNotificationTask(task=task, kwargs=kwargs),
        )

    def collect_notification_tasks(self) -> list[PendingNotificationTask]:
        tasks = self._pending_notifications
        self._pending_notifications = []
        return tasks

    async def list_comments(self, card_id: uuid.UUID) -> list[Comment]:
        return await self.repository.list_by_card(card_id)

    async def create_comment(
        self,
        board_id: uuid.UUID,
        card_id: uuid.UUID,
        author_id: uuid.UUID,
        body: str,
        author_name: str,
    ) -> Comment:
        comment = Comment(
            card_id=card_id,
            author_id=author_id,
            body=body,
        )
        created = await self.repository.create(comment)

        mentioned_users = await self._resolve_mentions(body)

        for user_id in mentioned_users:
            mention = CommentMention(
                comment_id=created.id,
                mentioned_user_id=user_id,
            )
            await self.repository.add_mention(mention)

        await self.activity_service.record(
            board_id=board_id,
            actor_id=author_id,
            action="comment.created",
            entity_type="comment",
            entity_id=created.id,
            meta={"mentions": [str(uid) for uid in mentioned_users]},
        )

        reloaded = await self._reload(created.id)

        card = await self.session.get(Card, card_id)
        card_title = card.title if card is not None else ""

        for user_id in mentioned_users:
            if user_id == author_id:
                continue
            self._queue_notification(
                notify_card_mentioned,
                user_id=str(user_id),
                author_name=author_name,
                card_id=str(card_id),
                card_title=card_title,
                board_id=str(board_id),
            )

        self._queue_event(
            RealtimeEvent(
                type=EventType.COMMENT_CREATED,
                board_id=str(board_id),
                actor_id=str(author_id),
                payload={
                    "id": str(reloaded.id),
                    "card_id": str(card_id),
                    "mentions": [str(uid) for uid in mentioned_users],
                },
            ),
        )

        return reloaded

    async def _resolve_mentions(self, body: str) -> list[uuid.UUID]:
        usernames = set(MENTION_PATTERN.findall(body))

        if not usernames:
            return []

        stmt = select(User).where(
            User.email.in_([f"{name}" for name in usernames]),
        )
        result = await self.session.execute(stmt)
        matched = list(result.scalars().all())

        if not matched:
            all_users_stmt = select(User)
            all_result = await self.session.execute(all_users_stmt)
            all_users = list(all_result.scalars().all())

            matched = [user for user in all_users if user.email.split("@")[0] in usernames]

        return [user.id for user in matched]

    async def _reload(self, comment_id: uuid.UUID) -> Comment:
        stmt = (
            select(Comment).where(Comment.id == comment_id).options(selectinload(Comment.mentions))
        )
        result = await self.session.execute(stmt)
        comment = result.scalar_one()
        return comment
