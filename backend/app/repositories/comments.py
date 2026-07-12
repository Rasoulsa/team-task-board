from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comment import Comment, CommentMention


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_card(self, card_id: uuid.UUID) -> list[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.card_id == card_id)
            .options(selectinload(Comment.mentions))
            .order_by(Comment.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, comment: Comment) -> Comment:
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def add_mention(self, mention: CommentMention) -> CommentMention:
        self.session.add(mention)
        await self.session.flush()
        return mention
