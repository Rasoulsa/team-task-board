from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_assigning_same_user_twice_does_not_create_duplicate(
    authenticated_user: dict[str, str],
    seed_board_with_column: dict[str, str],
) -> None:
    client: AsyncClient = authenticated_user["client"]
    user_id = authenticated_user["user_id"]
    column_id = seed_board_with_column["column_id"]

    # Create a card. Adjust the endpoint to match test_cards.py.
    card_response = await client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={"title": "Assignee dedup card"},
    )
    assert card_response.status_code == 201, card_response.text
    card_id = card_response.json()["id"]

    payload = {"user_id": user_id}

    first = await client.post(
        f"/api/v1/cards/{card_id}/assignees",
        json=payload,
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        f"/api/v1/cards/{card_id}/assignees",
        json=payload,
    )
    assert second.status_code == 201, second.text

    card = await client.get(f"/api/v1/cards/{card_id}")
    assert card.status_code == 200, card.text

    matching = [
        assignment for assignment in card.json()["assignees"] if assignment["user_id"] == user_id
    ]
    assert len(matching) == 1


@pytest.mark.asyncio
async def test_remove_assignee_is_idempotent(
    authenticated_user: dict[str, str],
    seed_board_with_column: dict[str, str],
) -> None:
    client: AsyncClient = authenticated_user["client"]
    user_id = authenticated_user["user_id"]
    column_id = seed_board_with_column["column_id"]

    card_response = await client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={"title": "Assignee removal card"},
    )
    assert card_response.status_code == 201, card_response.text
    card_id = card_response.json()["id"]

    assign = await client.post(
        f"/api/v1/cards/{card_id}/assignees",
        json={"user_id": user_id},
    )
    assert assign.status_code == 201, assign.text

    delete_one = await client.delete(
        f"/api/v1/cards/{card_id}/assignees/{user_id}",
    )
    assert delete_one.status_code == 204, delete_one.text

    delete_again = await client.delete(
        f"/api/v1/cards/{card_id}/assignees/{user_id}",
    )
    assert delete_again.status_code == 204, delete_again.text

    card = await client.get(f"/api/v1/cards/{card_id}")
    assert card.status_code == 200, card.text

    matching = [
        assignment for assignment in card.json()["assignees"] if assignment["user_id"] == user_id
    ]
    assert matching == []
