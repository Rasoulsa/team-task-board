from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentMentionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mentioned_user_id: uuid.UUID


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    card_id: uuid.UUID
    author_id: uuid.UUID
    body: str
    created_at: datetime

    mentions: list[CommentMentionRead] = Field(default_factory=list)


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
