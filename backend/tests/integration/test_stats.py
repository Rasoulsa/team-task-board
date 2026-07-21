import pytest


@pytest.mark.asyncio
async def test_board_stats_shape(
    authed_client,
    seed_board_with_column: dict[str, str],
) -> None:
    board_id = seed_board_with_column["board_id"]
    column_id = seed_board_with_column["column_id"]

    # Create one card in the (non-done) "Todo" column.
    created = await authed_client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={"title": "Open card"},
    )
    assert created.status_code == 201, created.text

    stats = await authed_client.get(f"/api/v1/boards/{board_id}/stats")
    assert stats.status_code == 200, stats.text
    body = stats.json()

    assert body["board_id"] == board_id
    assert set(body["totals"].keys()) == {
        "open_count",
        "closed_count",
        "overdue_count",
        "total_count",
    }
    assert isinstance(body["per_member"], list)

    totals = body["totals"]
    # One active card in an open column.
    assert totals["total_count"] >= 1
    assert totals["open_count"] >= 1
    assert totals["closed_count"] == 0
    assert totals["overdue_count"] == 0


@pytest.mark.asyncio
async def test_board_stats_counts_closed_cards(
    authed_client,
    seed_board_with_two_columns: dict[str, str],
) -> None:
    """A card in the board's done column counts as closed."""
    board_id = seed_board_with_two_columns["board_id"]

    kanban = await authed_client.get(f"/api/v1/boards/{board_id}/kanban")
    assert kanban.status_code == 200, kanban.text
    columns = kanban.json()["columns"]

    done_col = next(c for c in columns if c["is_done_column"])
    open_col = next(c for c in columns if not c["is_done_column"])

    r_done = await authed_client.post(
        f"/api/v1/columns/{done_col['id']}/cards",
        json={"title": "Closed card"},
    )
    assert r_done.status_code == 201, r_done.text

    r_open = await authed_client.post(
        f"/api/v1/columns/{open_col['id']}/cards",
        json={"title": "Open card"},
    )
    assert r_open.status_code == 201, r_open.text

    stats = await authed_client.get(f"/api/v1/boards/{board_id}/stats")
    assert stats.status_code == 200, stats.text
    totals = stats.json()["totals"]

    assert totals["total_count"] >= 2
    assert totals["closed_count"] >= 1
    assert totals["open_count"] >= 1
