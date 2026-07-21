import pytest

from app.core.board_cache import _board_key
from app.main import app


@pytest.mark.asyncio
async def test_kanban_cached_then_invalidated(
    authed_client,
    seed_board_with_column: dict[str, str],
) -> None:
    board_id = seed_board_with_column["board_id"]
    column_id = seed_board_with_column["column_id"]

    redis = app.state.redis
    key = _board_key(board_id)

    # Ensure a clean slate.
    await redis.delete(key)
    assert await redis.get(key) is None

    # First read populates the cache.
    r1 = await authed_client.get(f"/api/v1/boards/{board_id}/kanban")
    assert r1.status_code == 200, r1.text
    assert await redis.get(key) is not None

    # Second read is served from cache and returns the same payload.
    r2 = await authed_client.get(f"/api/v1/boards/{board_id}/kanban")
    assert r2.status_code == 200, r2.text
    assert r2.json() == r1.json()

    # A mutation must invalidate the board cache.
    created = await authed_client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={"title": "Invalidator"},
    )
    assert created.status_code == 201, created.text
    assert await redis.get(key) is None

    # Next read repopulates and now reflects the new card.
    r3 = await authed_client.get(f"/api/v1/boards/{board_id}/kanban")
    assert r3.status_code == 200, r3.text
    assert await redis.get(key) is not None
    assert r3.json() != r1.json()  # cache reflects the mutation
