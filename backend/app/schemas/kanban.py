from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class KanbanLabelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    color: str


class KanbanAssigneeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID


class KanbanChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str
    is_done: bool
    position: int


class KanbanCardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    column_id: UUID
    title: str
    description: str | None = None
    priority: str = "medium"
    due_date: datetime | None = None
    rank: str
    is_deleted: bool = False

    labels: list[KanbanLabelRead] = Field(default_factory=list)
    assignees: list[KanbanAssigneeRead] = Field(default_factory=list)

    # ORM attribute is `checklist_items`; expose it as `checklist`
    # to the frontend using a validation alias.
    checklist: list[KanbanChecklistItemRead] = Field(
        default_factory=list,
        validation_alias="checklist_items",
    )


class KanbanColumnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    board_id: UUID
    name: str
    position: int
    is_done_column: bool

    cards: list[KanbanCardRead] = Field(default_factory=list)


class KanbanBoard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    columns: list[KanbanColumnRead] = Field(default_factory=list)
