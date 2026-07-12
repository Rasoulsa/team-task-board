from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CardLabelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    color: str


class CardAssigneeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID


class ChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    is_done: bool
    position: int


class CardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    column_id: uuid.UUID
    title: str
    description: str | None
    priority: str
    rank: str
    due_date: datetime | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    labels: list[CardLabelRead] = Field(default_factory=list)
    assignees: list[CardAssigneeRead] = Field(default_factory=list)
    checklist_items: list[ChecklistItemRead] = Field(default_factory=list)


class CardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: str = Field(default="medium")
    due_date: datetime | None = None


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: str | None = None
    due_date: datetime | None = None


class CardMove(BaseModel):
    target_column_id: uuid.UUID
    previous_card_id: uuid.UUID | None = None
    next_card_id: uuid.UUID | None = None


class CardLabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="gray", max_length=20)


class CardAssigneeCreate(BaseModel):
    user_id: uuid.UUID


class ChecklistItemCreate(BaseModel):
    content: str = Field(min_length=1, max_length=255)


class ChecklistItemUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1, max_length=255)
    is_done: bool | None = None
