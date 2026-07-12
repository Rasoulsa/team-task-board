from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment, CommentMention
from app.models.user import User
from app.repositories.comments import CommentRepository
from app.services.activity import ActivityService

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

    async def list_comments(self, card_id: uuid.UUID) -> list[Comment]:
        return await self.repository.list_by_card(card_id)

    async def create_comment(
        self,
        board_id: uuid.UUID,
        card_id: uuid.UUID,
        author_id: uuid.UUID,
        body: str,
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

        return await self._reload(created.id)

    async def _resolve_mentions(self, body: str) -> list[uuid.UUID]:
        usernames = set(MENTION_PATTERN.findall(body))

        if not usernames:
            return []

        # We match against email local-part or full email prefix.
        stmt = select(User).where(User.email.in_([f"{name}" for name in usernames]))
        result = await self.session.execute(stmt)
        matched = list(result.scalars().all())

        # Also try email local-part matching.
        if not matched:
            all_users_stmt = select(User)
            all_result = await self.session.execute(all_users_stmt)
            all_users = list(all_result.scalars().all())

            matched = [user for user in all_users if user.email.split("@")[0] in usernames]

        return [user.id for user in matched]

    async def _reload(self, comment_id: uuid.UUID) -> Comment:
        from sqlalchemy.orm import selectinload

        stmt = (
            select(Comment).where(Comment.id == comment_id).options(selectinload(Comment.mentions))
        )
        result = await self.session.execute(stmt)
        comment = result.scalar_one()
        return comment
