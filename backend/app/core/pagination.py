from __future__ import annotations

import base64
import binascii
import json
from datetime import datetime

from pydantic import BaseModel


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int


class CursorPage[T](BaseModel):
    items: list[T]
    next_cursor: str | None


def encode_cursor(*, created_at: datetime, item_id: str) -> str:
    raw = json.dumps(
        {"ts": created_at.isoformat(), "id": str(item_id)},
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        data = json.loads(raw)
        return datetime.fromisoformat(data["ts"]), str(data["id"])
    except (binascii.Error, ValueError, KeyError, TypeError) as exc:
        raise ValueError("Invalid cursor") from exc
