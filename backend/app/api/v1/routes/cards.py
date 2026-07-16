from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.board_access import (
    get_board_and_org_for_card,
    get_board_and_org_for_column,
)
from app.api.deps import (
    get_current_user,
    get_db_session,
    get_event_bridge,
)
from app.api.rbac import require_org_role
from app.models.enums import OrganizationRole
from app.models.user import User
from app.repositories.activity import ActivityRepository
from app.repositories.cards import CardRepository
from app.schemas.card import (
    CardAssigneeCreate,
    CardAssigneeRead,
    CardCreate,
    CardLabelCreate,
    CardLabelRead,
    CardMove,
    CardRead,
    CardUpdate,
    ChecklistItemCreate,
    ChecklistItemRead,
    ChecklistItemUpdate,
)
from app.services.activity import ActivityService
from app.services.cards import CardService
from app.services.notification_dispatch import enqueue_notifications
from app.ws.pubsub import RedisEventBridge

router = APIRouter(tags=["cards"])


def build_card_service(session: AsyncSession) -> CardService:
    activity_service = ActivityService(ActivityRepository(session))
    return CardService(CardRepository(session), activity_service)


async def _publish(
    event_bridge: RedisEventBridge,
    service: CardService,
) -> None:
    for event in service.collect_events():
        await event_bridge.publish(event)


@router.get(
    "/columns/{column_id}/cards",
    response_model=list[CardRead],
)
async def list_cards(
    column_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[CardRead]:
    _, org_id = await get_board_and_org_for_column(session, column_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.VIEWER,
    )

    service = build_card_service(session)
    cards = await service.list_cards(column_id)
    return [CardRead.model_validate(card) for card in cards]


@router.post(
    "/columns/{column_id}/cards",
    response_model=CardRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_card(
    column_id: uuid.UUID,
    payload: CardCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
) -> CardRead:
    board_id, org_id = await get_board_and_org_for_column(session, column_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )

    service = build_card_service(session)
    card = await service.create_card(
        board_id=board_id,
        column_id=column_id,
        actor_id=current_user.id,
        payload=payload,
    )
    await session.commit()
    await _publish(event_bridge, service)
    return CardRead.model_validate(card)


@router.get("/cards/{card_id}", response_model=CardRead)
async def get_card(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CardRead:
    _, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.VIEWER,
    )

    service = build_card_service(session)
    card = await service.get_card(card_id)
    return CardRead.model_validate(card)


@router.patch("/cards/{card_id}", response_model=CardRead)
async def update_card(
    card_id: uuid.UUID,
    payload: CardUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
) -> CardRead:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )

    service = build_card_service(session)
    card = await service.update_card(
        board_id=board_id,
        card_id=card_id,
        actor_id=current_user.id,
        payload=payload,
    )
    await session.commit()
    await _publish(event_bridge, service)
    return CardRead.model_validate(card)


@router.post("/cards/{card_id}/move", response_model=CardRead)
async def move_card(
    card_id: uuid.UUID,
    payload: CardMove,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
) -> CardRead:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )

    service = build_card_service(session)
    card = await service.move_card(
        board_id=board_id,
        card_id=card_id,
        actor_id=current_user.id,
        payload=payload,
    )
    await session.commit()
    await _publish(event_bridge, service)
    return CardRead.model_validate(card)


@router.delete(
    "/cards/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_card(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
) -> None:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )

    service = build_card_service(session)
    await service.delete_card(
        board_id=board_id,
        card_id=card_id,
        actor_id=current_user.id,
    )
    await session.commit()
    await _publish(event_bridge, service)


@router.post("/cards/{card_id}/restore", response_model=CardRead)
async def restore_card(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
) -> CardRead:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )

    service = build_card_service(session)
    card = await service.restore_card(
        board_id=board_id,
        card_id=card_id,
        actor_id=current_user.id,
    )
    await session.commit()
    await _publish(event_bridge, service)
    return CardRead.model_validate(card)


@router.post(
    "/cards/{card_id}/labels",
    response_model=CardLabelRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_label(
    card_id: uuid.UUID,
    payload: CardLabelCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
) -> CardLabelRead:
    _, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )

    service = build_card_service(session)
    label = await service.add_label(card_id, payload)
    await session.commit()
    await _publish(event_bridge, service)
    return CardLabelRead.model_validate(label)


@router.post(
    "/cards/{card_id}/assignees",
    response_model=CardAssigneeRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_assignee(
    card_id: uuid.UUID,
    payload: CardAssigneeCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
) -> CardAssigneeRead:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )

    service = build_card_service(session)
    assignee = await service.add_assignee(
        card_id,
        payload,
        board_id=board_id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
    )
    await session.commit()
    await _publish(event_bridge, service)
    enqueue_notifications(service)
    return CardAssigneeRead.model_validate(assignee)


@router.post(
    "/cards/{card_id}/checklist",
    response_model=ChecklistItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_checklist_item(
    card_id: uuid.UUID,
    payload: ChecklistItemCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
) -> ChecklistItemRead:
    _, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )

    service = build_card_service(session)
    item = await service.add_checklist_item(card_id, payload)
    await session.commit()
    await _publish(event_bridge, service)
    return ChecklistItemRead.model_validate(item)


@router.patch(
    "/checklist/{item_id}",
    response_model=ChecklistItemRead,
)
async def update_checklist_item(
    item_id: uuid.UUID,
    payload: ChecklistItemUpdate,
    session: AsyncSession = Depends(get_db_session),
    _current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
) -> ChecklistItemRead:
    service = build_card_service(session)
    item = await service.update_checklist_item(item_id, payload)
    await session.commit()
    await _publish(event_bridge, service)
    return ChecklistItemRead.model_validate(item)
