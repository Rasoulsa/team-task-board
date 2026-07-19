from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.card import (
    Card,
    CardAssignee,
    CardLabel,
    ChecklistItem,
)


class CardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_column(
        self,
        column_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> list[Card]:
        stmt = (
            select(Card)
            .where(Card.column_id == column_id)
            .options(
                selectinload(Card.labels),
                selectinload(Card.assignees),
                selectinload(Card.checklist_items),
            )
            .order_by(Card.rank.asc())
        )

        if not include_deleted:
            stmt = stmt.where(Card.is_deleted.is_(False))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, card_id: uuid.UUID) -> Card | None:
        stmt = (
            select(Card)
            .where(Card.id == card_id)
            .options(
                selectinload(Card.labels),
                selectinload(Card.assignees),
                selectinload(Card.checklist_items),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_last_rank_in_column(
        self,
        column_id: uuid.UUID,
    ) -> str | None:
        stmt = (
            select(Card.rank)
            .where(
                Card.column_id == column_id,
                Card.is_deleted.is_(False),
            )
            .order_by(Card.rank.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, card: Card) -> Card:
        self.session.add(card)
        await self.session.flush()
        return card

    async def soft_delete(self, card: Card) -> None:
        card.is_deleted = True
        card.deleted_at = datetime.now(UTC)
        await self.session.flush()

    async def restore(self, card: Card) -> None:
        card.is_deleted = False
        card.deleted_at = None
        await self.session.flush()

    async def add_label(self, label: CardLabel) -> CardLabel:
        self.session.add(label)
        await self.session.flush()
        return label

    async def add_assignee(
        self,
        assignee: CardAssignee,
    ) -> CardAssignee:
        self.session.add(assignee)
        await self.session.flush()
        return assignee

    async def get_assignee(
        self,
        card_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CardAssignee | None:
        stmt = select(CardAssignee).where(
            CardAssignee.card_id == card_id,
            CardAssignee.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_assignee(
        self,
        card_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        assignee = await self.get_assignee(
            card_id=card_id,
            user_id=user_id,
        )

        if assignee is None:
            return False

        await self.session.delete(assignee)
        await self.session.flush()
        return True

    async def add_checklist_item(
        self,
        item: ChecklistItem,
    ) -> ChecklistItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_checklist_item(
        self,
        item_id: uuid.UUID,
    ) -> ChecklistItem | None:
        stmt = select(ChecklistItem).where(ChecklistItem.id == item_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_assigned_to_user(
        self,
        user_id: uuid.UUID,
    ) -> list[Card]:
        stmt = (
            select(Card)
            .join(CardAssignee, CardAssignee.card_id == Card.id)
            .where(
                CardAssignee.user_id == user_id,
                Card.is_deleted.is_(False),
            )
            .options(
                selectinload(Card.labels),
                selectinload(Card.assignees),
                selectinload(Card.checklist_items),
            )
            .order_by(Card.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())
