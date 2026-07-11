import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ColumnCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    position: int | None = None


class ColumnUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    position: int | None = None


class ColumnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    board_id: uuid.UUID
    name: str
    position: int
    created_at: datetime
    updated_at: datetime
