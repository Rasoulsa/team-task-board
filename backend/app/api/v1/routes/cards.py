from __future__ import annotations

import contextlib
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.board_access import (
    get_board_and_org_for_card,
    get_board_and_org_for_column,
)
from app.api.card_access import require_card_read_access
from app.api.deps import (
    get_current_user,
    get_db_session,
    get_event_bridge,
    get_redis,
)
from app.api.rbac import get_membership, require_org_role
from app.core.board_cache import invalidate_board
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


async def _publish(event_bridge: RedisEventBridge, service: CardService) -> None:
    for event in service.collect_events():
        await event_bridge.publish(event)


async def _finalize(
    *,
    session: AsyncSession,
    event_bridge: RedisEventBridge,
    redis: Redis,
    service: CardService,
    board_id: uuid.UUID,
) -> None:
    await session.commit()
    # best-effort cache invalidation; never fail the mutation
    with contextlib.suppress(Exception):
        await invalidate_board(redis, board_id)
    await _publish(event_bridge, service)


@router.get("/columns/{column_id}/cards", response_model=list[CardRead])
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


@router.get("/me/assigned-cards", response_model=list[CardRead])
async def list_my_assigned_cards(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[CardRead]:
    service = build_card_service(session)
    cards = await service.list_assigned_cards(current_user.id)
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
    redis: Redis = Depends(get_redis),
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
    await _finalize(
        session=session,
        event_bridge=event_bridge,
        redis=redis,
        service=service,
        board_id=board_id,
    )
    return CardRead.model_validate(card)


@router.get("/cards/{card_id}", response_model=CardRead)
async def get_card(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CardRead:
    await require_card_read_access(session, card_id=card_id, current_user=current_user)
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
    redis: Redis = Depends(get_redis),
) -> CardRead:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)

    membership = await get_membership(
        session=session,
        organization_id=org_id,
        user_id=current_user.id,
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this card",
        )

    service = build_card_service(session)

    if membership.role == OrganizationRole.GUEST:
        from app.api.card_access import _is_assignee

        if not await _is_assignee(session, card_id=card_id, user_id=current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only edit cards assigned to you",
            )
        provided = payload.model_dump(exclude_unset=True)
        disallowed = set(provided.keys()) - {"description"}
        if disallowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Guests may only edit the description",
            )
        card = await service.update_card_description(
            board_id=board_id,
            card_id=card_id,
            actor_id=current_user.id,
            description=payload.description,
        )
        await _finalize(
            session=session,
            event_bridge=event_bridge,
            redis=redis,
            service=service,
            board_id=board_id,
        )
        return CardRead.model_validate(card)

    from app.api.rbac import role_allows

    if not role_allows(membership.role, OrganizationRole.MEMBER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    card = await service.update_card(
        board_id=board_id,
        card_id=card_id,
        actor_id=current_user.id,
        payload=payload,
    )
    await _finalize(
        session=session,
        event_bridge=event_bridge,
        redis=redis,
        service=service,
        board_id=board_id,
    )
    return CardRead.model_validate(card)


@router.post("/cards/{card_id}/move", response_model=CardRead)
async def move_card(
    card_id: uuid.UUID,
    payload: CardMove,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
    redis: Redis = Depends(get_redis),
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
    await _finalize(
        session=session,
        event_bridge=event_bridge,
        redis=redis,
        service=service,
        board_id=board_id,
    )
    return CardRead.model_validate(card)


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
    redis: Redis = Depends(get_redis),
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
    await _finalize(
        session=session,
        event_bridge=event_bridge,
        redis=redis,
        service=service,
        board_id=board_id,
    )


@router.post("/cards/{card_id}/restore", response_model=CardRead)
async def restore_card(
    card_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
    redis: Redis = Depends(get_redis),
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
    await _finalize(
        session=session,
        event_bridge=event_bridge,
        redis=redis,
        service=service,
        board_id=board_id,
    )
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
    redis: Redis = Depends(get_redis),
) -> CardLabelRead:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )
    service = build_card_service(session)
    label = await service.add_label(card_id, payload)
    await _finalize(
        session=session,
        event_bridge=event_bridge,
        redis=redis,
        service=service,
        board_id=board_id,
    )
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
    redis: Redis = Depends(get_redis),
) -> CardAssigneeRead:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )
    target_membership = await get_membership(
        session=session,
        organization_id=org_id,
        user_id=payload.user_id,
    )
    if target_membership is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The selected user is not a member of this card's organization",
        )
    service = build_card_service(session)
    assignee = await service.add_assignee(
        card_id,
        payload,
        board_id=board_id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
    )
    await _finalize(
        session=session,
        event_bridge=event_bridge,
        redis=redis,
        service=service,
        board_id=board_id,
    )
    enqueue_notifications(service)
    return CardAssigneeRead.model_validate(assignee)


@router.delete(
    "/cards/{card_id}/assignees/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_assignee(
    card_id: uuid.UUID,
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
    redis: Redis = Depends(get_redis),
) -> None:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )
    service = build_card_service(session)
    await service.remove_assignee(
        card_id=card_id,
        user_id=user_id,
        board_id=board_id,
        actor_id=current_user.id,
    )
    await _finalize(
        session=session,
        event_bridge=event_bridge,
        redis=redis,
        service=service,
        board_id=board_id,
    )


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
    redis: Redis = Depends(get_redis),
) -> ChecklistItemRead:
    board_id, org_id = await get_board_and_org_for_card(session, card_id)
    await require_org_role(
        session=session,
        organization_id=org_id,
        current_user=current_user,
        minimum_role=OrganizationRole.MEMBER,
    )
    service = build_card_service(session)
    item = await service.add_checklist_item(card_id, payload)
    await _finalize(
        session=session,
        event_bridge=event_bridge,
        redis=redis,
        service=service,
        board_id=board_id,
    )
    return ChecklistItemRead.model_validate(item)


@router.patch("/checklist/{item_id}", response_model=ChecklistItemRead)
async def update_checklist_item(
    item_id: uuid.UUID,
    payload: ChecklistItemUpdate,
    session: AsyncSession = Depends(get_db_session),
    _current_user: User = Depends(get_current_user),
    event_bridge: RedisEventBridge = Depends(get_event_bridge),
    redis: Redis = Depends(get_redis),
) -> ChecklistItemRead:
    service = build_card_service(session)
    item = await service.update_checklist_item(item_id, payload)
    await session.commit()

    # Resolve the owning board to invalidate its cache.
    board_id, _ = await get_board_and_org_for_card(session, item.card_id)
    with contextlib.suppress(Exception):
        await invalidate_board(redis, board_id)
    await _publish(event_bridge, service)
    return ChecklistItemRead.model_validate(item)
