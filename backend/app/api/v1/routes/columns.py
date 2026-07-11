import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.column import ColumnCreate, ColumnRead, ColumnUpdate
from app.services.columns import ColumnService

router = APIRouter(tags=["columns"])


@router.get("/boards/{board_id}/columns", response_model=list[ColumnRead])
async def list_columns(
    board_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ColumnRead]:
    service = ColumnService(session)
    columns = await service.list_columns(
        board_id=board_id,
        current_user=current_user,
    )
    return [ColumnRead.model_validate(column) for column in columns]


@router.post(
    "/boards/{board_id}/columns",
    response_model=ColumnRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_column(
    board_id: uuid.UUID,
    payload: ColumnCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ColumnRead:
    service = ColumnService(session)
    column = await service.create_column(
        board_id=board_id,
        name=payload.name,
        position=payload.position,
        current_user=current_user,
    )
    return ColumnRead.model_validate(column)


@router.patch("/columns/{column_id}", response_model=ColumnRead)
async def update_column(
    column_id: uuid.UUID,
    payload: ColumnUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ColumnRead:
    service = ColumnService(session)
    column = await service.update_column(
        column_id=column_id,
        name=payload.name,
        position=payload.position,
        current_user=current_user,
    )
    return ColumnRead.model_validate(column)


@router.delete("/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(
    column_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    service = ColumnService(session)
    await service.delete_column(
        column_id=column_id,
        current_user=current_user,
    )
