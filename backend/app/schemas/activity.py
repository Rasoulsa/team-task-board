from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ActivityRead(BaseModel):
    id: uuid.UUID
    board_id: uuid.UUID
    actor_id: uuid.UUID | None
    actor_name: str | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    meta: dict[str, Any]
    created_at: datetime
