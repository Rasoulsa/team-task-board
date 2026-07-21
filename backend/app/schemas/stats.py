from __future__ import annotations

import uuid

from pydantic import BaseModel


class MemberCardStats(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: str
    open_count: int
    closed_count: int
    overdue_count: int


class BoardTotalsRead(BaseModel):
    open_count: int
    closed_count: int
    overdue_count: int
    total_count: int


class BoardStats(BaseModel):
    board_id: uuid.UUID
    totals: BoardTotalsRead
    per_member: list[MemberCardStats]
