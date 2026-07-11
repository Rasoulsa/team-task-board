import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.board import BoardCreate, BoardRead, BoardUpdate
from app.services.boards import BoardService

router = APIRouter(tags=["boards"])


@router.get("/projects/{project_id}/boards", response_model=list[BoardRead])
async def list_boards(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BoardRead]:
    service = BoardService(session)
    boards = await service.list_boards(
        project_id=project_id,
        current_user=current_user,
    )
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


@router.get("/boards/{board_id}", response_model=BoardRead)
async def get_board(
    board_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoardRead:
    service = BoardService(session)
    board = await service.get_board(
        board_id=board_id,
        current_user=current_user,
    )
    return BoardRead.model_validate(board)


@router.patch("/boards/{board_id}", response_model=BoardRead)
async def update_board(
    board_id: uuid.UUID,
    payload: BoardUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BoardRead:
    service = BoardService(session)
    board = await service.update_board(
        board_id=board_id,
        name=payload.name,
        description=payload.description,
        current_user=current_user,
    )
    return BoardRead.model_validate(board)


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = BoardService(session)
    await service.delete_board(
        board_id=board_id,
        current_user=current_user,
    )
