import contextlib
import uuid

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis
from app.core.board_cache import get_cached_board, invalidate_board, set_cached_board
from app.models.user import User
from app.schemas.board import BoardCreate, BoardRead, BoardUpdate
from app.schemas.kanban import KanbanBoard as KanbanBoardSchema
from app.schemas.organization import OrganizationMemberRead
from app.services.boards import BoardService

router = APIRouter(tags=["boards"])


async def invalidate_board_safe(redis: Redis, board_id: uuid.UUID) -> None:
    # best-effort; never fail the request on cache errors
    with contextlib.suppress(Exception):
        await invalidate_board(redis, board_id)


@router.get("/projects/{project_id}/boards", response_model=list[BoardRead])
async def list_boards(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BoardRead]:
    service = BoardService(session)
    boards = await service.list_boards(project_id=project_id, current_user=current_user)
    return [BoardRead.model_validate(board) for board in boards]


@router.post(
    "/projects/{project_id}/boards",
    response_model=BoardRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_board(
    project_id: uuid.UUID,
    payload: BoardCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoardRead:
    service = BoardService(session)
    board = await service.create_board(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        current_user=current_user,
    )

    return BoardRead.model_validate(board)


@router.get("/boards/{board_id}/kanban", response_model=KanbanBoardSchema)
async def get_kanban_board(
    board_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> KanbanBoardSchema:
    service = BoardService(session)

    # Authorization runs on EVERY request, even cache hits — no data leak.
    await service.get_board(board_id=board_id, current_user=current_user)

    cached = await get_cached_board(redis, board_id)
    if cached is not None:
        return KanbanBoardSchema.model_validate_json(cached)

    board = await service.get_kanban_board(board_id=board_id, current_user=current_user)
    schema = KanbanBoardSchema.model_validate(board)
    await set_cached_board(redis, board_id, schema.model_dump_json())
    return schema


@router.get("/boards/{board_id}", response_model=BoardRead)
async def get_board(
    board_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoardRead:
    service = BoardService(session)
    board = await service.get_board(board_id=board_id, current_user=current_user)
    return BoardRead.model_validate(board)


@router.patch("/boards/{board_id}", response_model=BoardRead)
async def update_board(
    board_id: uuid.UUID,
    payload: BoardUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> BoardRead:
    service = BoardService(session)
    board = await service.update_board(
        board_id=board_id,
        name=payload.name,
        description=payload.description,
        current_user=current_user,
    )
    await invalidate_board_safe(redis, board_id)
    return BoardRead.model_validate(board)


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> None:
    service = BoardService(session)
    await service.delete_board(board_id=board_id, current_user=current_user)
    await invalidate_board_safe(redis, board_id)


@router.get("/boards/{board_id}/members", response_model=list[OrganizationMemberRead])
async def list_board_members(
    board_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrganizationMemberRead]:
    service = BoardService(session)
    members = await service.list_members(board_id=board_id, current_user=current_user)
    return [
        OrganizationMemberRead(
            id=member.id,
            user_id=member.user_id,
            organization_id=member.organization_id,
            full_name=member.user.full_name,
            email=member.user.email,
            role=member.role,
            created_at=member.created_at,
        )
        for member in members
    ]
