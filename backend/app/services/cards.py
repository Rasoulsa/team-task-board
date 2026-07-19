from __future__ import annotations

import uuid
from typing import Any

from app.core.exceptions import NotFoundException
from app.models.card import (
    Card,
    CardAssignee,
    CardLabel,
    ChecklistItem,
)
from app.repositories.cards import CardRepository
from app.schemas.card import (
    CardAssigneeCreate,
    CardCreate,
    CardLabelCreate,
    CardMove,
    CardUpdate,
    ChecklistItemCreate,
    ChecklistItemUpdate,
)
from app.services.activity import ActivityService
from app.services.notification_dispatch import PendingNotificationTask
from app.utils.lexorank import rank_between
from app.worker.tasks import notify_card_assigned
from app.ws.events import EventType, RealtimeEvent


class CardService:
    def __init__(
        self,
        repository: CardRepository,
        activity_service: ActivityService,
    ) -> None:
        self.repository = repository
        self.activity_service = activity_service
        self._pending_events: list[RealtimeEvent] = []
        self._pending_notifications: list[PendingNotificationTask] = []

    def _queue_event(self, event: RealtimeEvent) -> None:
        self._pending_events.append(event)

    def collect_events(self) -> list[RealtimeEvent]:
        """Return queued events and clear the buffer.

        The caller is responsible for publishing these events, and
        should do so only after the surrounding transaction commits.
        """
        events = self._pending_events
        self._pending_events = []
        return events

    def _queue_notification(self, task: Any, **kwargs: Any) -> None:
        self._pending_notifications.append(
            PendingNotificationTask(task=task, kwargs=kwargs),
        )

    def collect_notification_tasks(self) -> list[PendingNotificationTask]:
        """Return queued notification tasks and clear the buffer.

        The caller is responsible for enqueuing these, and should do
        so only after the surrounding transaction commits.
        """
        tasks = self._pending_notifications
        self._pending_notifications = []
        return tasks

    async def list_cards(self, column_id: uuid.UUID) -> list[Card]:
        return await self.repository.list_by_column(column_id)

    async def get_card(self, card_id: uuid.UUID) -> Card:
        card = await self.repository.get(card_id)

        if card is None:
            raise NotFoundException("Card not found")

        return card

    async def create_card(
        self,
        board_id: uuid.UUID,
        column_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: CardCreate,
    ) -> Card:
        last_rank = await self.repository.get_last_rank_in_column(
            column_id,
        )
        new_rank = rank_between(last_rank, None)

        card = Card(
            column_id=column_id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            due_date=payload.due_date,
            rank=new_rank,
        )

        created = await self.repository.create(card)

        await self.activity_service.record(
            board_id=board_id,
            actor_id=actor_id,
            action="card.created",
            entity_type="card",
            entity_id=created.id,
            meta={"title": created.title},
        )

        full_card = await self.get_card(created.id)

        self._queue_event(
            RealtimeEvent(
                type=EventType.CARD_CREATED,
                board_id=str(board_id),
                actor_id=str(actor_id),
                payload={
                    "id": str(full_card.id),
                    "column_id": str(full_card.column_id),
                    "title": full_card.title,
                    "rank": full_card.rank,
                },
            ),
        )

        return full_card

    async def update_card(
        self,
        board_id: uuid.UUID,
        card_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: CardUpdate,
    ) -> Card:
        card = await self.get_card(card_id)

        if payload.title is not None:
            card.title = payload.title
        if payload.description is not None:
            card.description = payload.description
        if payload.priority is not None:
            card.priority = payload.priority
        if payload.due_date is not None:
            card.due_date = payload.due_date

        await self.repository.session.flush()

        await self.activity_service.record(
            board_id=board_id,
            actor_id=actor_id,
            action="card.updated",
            entity_type="card",
            entity_id=card.id,
            meta={},
        )

        updated = await self.get_card(card.id)

        self._queue_event(
            RealtimeEvent(
                type=EventType.CARD_UPDATED,
                board_id=str(board_id),
                actor_id=str(actor_id),
                payload={"id": str(updated.id)},
            ),
        )

        return updated

    async def move_card(
        self,
        board_id: uuid.UUID,
        card_id: uuid.UUID,
        actor_id: uuid.UUID,
        payload: CardMove,
    ) -> Card:
        card = await self.get_card(card_id)

        previous_rank: str | None = None
        next_rank: str | None = None

        if payload.previous_card_id is not None:
            previous = await self.get_card(payload.previous_card_id)
            previous_rank = previous.rank

        if payload.next_card_id is not None:
            following = await self.get_card(payload.next_card_id)
            next_rank = following.rank

        card.column_id = payload.target_column_id
        card.rank = rank_between(previous_rank, next_rank)

        await self.repository.session.flush()

        await self.activity_service.record(
            board_id=board_id,
            actor_id=actor_id,
            action="card.moved",
            entity_type="card",
            entity_id=card.id,
            meta={"column_id": str(payload.target_column_id)},
        )

        moved = await self.get_card(card.id)

        self._queue_event(
            RealtimeEvent(
                type=EventType.CARD_MOVED,
                board_id=str(board_id),
                actor_id=str(actor_id),
                payload={
                    "id": str(moved.id),
                    "column_id": str(moved.column_id),
                    "rank": moved.rank,
                },
            ),
        )

        return moved

    async def delete_card(
        self,
        board_id: uuid.UUID,
        card_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        card = await self.get_card(card_id)
        await self.repository.soft_delete(card)

        await self.activity_service.record(
            board_id=board_id,
            actor_id=actor_id,
            action="card.deleted",
            entity_type="card",
            entity_id=card.id,
            meta={},
        )

        self._queue_event(
            RealtimeEvent(
                type=EventType.CARD_DELETED,
                board_id=str(board_id),
                actor_id=str(actor_id),
                payload={"id": str(card.id)},
            ),
        )

    async def restore_card(
        self,
        board_id: uuid.UUID,
        card_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> Card:
        card = await self.repository.get(card_id)

        if card is None:
            raise NotFoundException("Card not found")

        await self.repository.restore(card)

        await self.activity_service.record(
            board_id=board_id,
            actor_id=actor_id,
            action="card.restored",
            entity_type="card",
            entity_id=card.id,
            meta={},
        )

        restored = await self.get_card(card.id)

        self._queue_event(
            RealtimeEvent(
                type=EventType.CARD_RESTORED,
                board_id=str(board_id),
                actor_id=str(actor_id),
                payload={
                    "id": str(restored.id),
                    "column_id": str(restored.column_id),
                    "rank": restored.rank,
                },
            ),
        )

        return restored

    async def add_label(
        self,
        card_id: uuid.UUID,
        payload: CardLabelCreate,
    ) -> CardLabel:
        await self.get_card(card_id)

        label = CardLabel(
            card_id=card_id,
            name=payload.name,
            color=payload.color,
        )
        return await self.repository.add_label(label)

    async def add_assignee(
        self,
        card_id: uuid.UUID,
        payload: CardAssigneeCreate,
        *,
        board_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_name: str,
    ) -> CardAssignee:
        card = await self.get_card(card_id)

        existing = await self.repository.get_assignee(
            card_id=card_id,
            user_id=payload.user_id,
        )

        if existing is not None:
            return existing

        assignee = CardAssignee(
            card_id=card_id,
            user_id=payload.user_id,
        )
        created = await self.repository.add_assignee(assignee)

        await self.activity_service.record(
            board_id=board_id,
            actor_id=actor_id,
            action="card.assignee_added",
            entity_type="card",
            entity_id=card.id,
            meta={"user_id": str(payload.user_id)},
        )

        self._queue_event(
            RealtimeEvent(
                type=EventType.CARD_UPDATED,
                board_id=str(board_id),
                actor_id=str(actor_id),
                payload={"id": str(card.id)},
            ),
        )

        if payload.user_id != actor_id:
            self._queue_notification(
                notify_card_assigned,
                user_id=str(payload.user_id),
                assigner_name=actor_name,
                card_id=str(card_id),
                card_title=card.title,
                board_id=str(board_id),
            )

        return created

    async def remove_assignee(
        self,
        card_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        board_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> None:
        card = await self.get_card(card_id)

        removed = await self.repository.remove_assignee(
            card_id=card_id,
            user_id=user_id,
        )

        if not removed:
            return

        await self.activity_service.record(
            board_id=board_id,
            actor_id=actor_id,
            action="card.assignee_removed",
            entity_type="card",
            entity_id=card.id,
            meta={"user_id": str(user_id)},
        )

        self._queue_event(
            RealtimeEvent(
                type=EventType.CARD_UPDATED,
                board_id=str(board_id),
                actor_id=str(actor_id),
                payload={"id": str(card.id)},
            ),
        )

    async def add_checklist_item(
        self,
        card_id: uuid.UUID,
        payload: ChecklistItemCreate,
    ) -> ChecklistItem:
        await self.get_card(card_id)

        item = ChecklistItem(
            card_id=card_id,
            content=payload.content,
        )
        return await self.repository.add_checklist_item(item)

    async def update_checklist_item(
        self,
        item_id: uuid.UUID,
        payload: ChecklistItemUpdate,
    ) -> ChecklistItem:
        item = await self.repository.get_checklist_item(item_id)

        if item is None:
            raise NotFoundException("Checklist item not found")

        if payload.content is not None:
            item.content = payload.content
        if payload.is_done is not None:
            item.is_done = payload.is_done

        await self.repository.session.flush()
        return item
    
    async def list_assigned_cards(
        self,
        user_id: uuid.UUID,
    ) -> list[Card]:
        return await self.repository.list_assigned_to_user(user_id)

    async def update_card_description(
        self,
        board_id: uuid.UUID,
        card_id: uuid.UUID,
        actor_id: uuid.UUID,
        description: str | None,
    ) -> Card:
        """Guest-safe update: only the description field may change."""
        card = await self.get_card(card_id)
        card.description = description

        await self.repository.session.flush()

        await self.activity_service.record(
            board_id=board_id,
            actor_id=actor_id,
            action="card.description_updated",
            entity_type="card",
            entity_id=card.id,
            meta={},
        )

        updated = await self.get_card(card.id)

        self._queue_event(
            RealtimeEvent(
                type=EventType.CARD_UPDATED,
                board_id=str(board_id),
                actor_id=str(actor_id),
                payload={"id": str(updated.id)},
            ),
        )

        return updated
