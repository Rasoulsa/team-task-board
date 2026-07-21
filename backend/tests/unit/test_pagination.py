from datetime import UTC, datetime

import pytest

from app.core.pagination import decode_cursor, encode_cursor


def test_cursor_roundtrip() -> None:
    ts = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    item_id = "11111111-1111-1111-1111-111111111111"
    decoded_ts, decoded_id = decode_cursor(encode_cursor(created_at=ts, item_id=item_id))
    assert decoded_ts == ts
    assert decoded_id == item_id


def test_invalid_cursor_raises() -> None:
    with pytest.raises(ValueError):
        decode_cursor("!!!not-valid!!!")
