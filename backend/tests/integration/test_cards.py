from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_and_list_cards(
    authed_client,
    seed_board_with_column,
):
    """Create a card in a column and list it back."""

    column_id = seed_board_with_column["column_id"]

    create_response = await authed_client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={
            "title": "First card",
            "description": "Card body",
            "priority": "high",
        },
    )
    assert create_response.status_code == 201

    created = create_response.json()
    assert created["title"] == "First card"
    assert created["rank"]

    list_response = await authed_client.get(
        f"/api/v1/columns/{column_id}/cards",
    )
    assert list_response.status_code == 200

    cards = list_response.json()
    assert len(cards) == 1
    assert cards[0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_cards_are_ordered_by_rank(
    authed_client,
    seed_board_with_column,
):
    column_id = seed_board_with_column["column_id"]

    titles = ["A", "B", "C"]

    for title in titles:
        response = await authed_client.post(
            f"/api/v1/columns/{column_id}/cards",
            json={"title": title},
        )
        assert response.status_code == 201

    list_response = await authed_client.get(
        f"/api/v1/columns/{column_id}/cards",
    )
    cards = list_response.json()

    ranks = [card["rank"] for card in cards]
    assert ranks == sorted(ranks)

    returned_titles = [card["title"] for card in cards]
    assert returned_titles == titles


@pytest.mark.asyncio
async def test_soft_delete_and_restore_card(
    authed_client,
    seed_board_with_column,
):
    column_id = seed_board_with_column["column_id"]

    create_response = await authed_client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={"title": "Deletable"},
    )
    card_id = create_response.json()["id"]

    delete_response = await authed_client.delete(
        f"/api/v1/cards/{card_id}",
    )
    assert delete_response.status_code == 204

    list_response = await authed_client.get(
        f"/api/v1/columns/{column_id}/cards",
    )
    assert list_response.json() == []

    restore_response = await authed_client.post(
        f"/api/v1/cards/{card_id}/restore",
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["is_deleted"] is False

    list_again = await authed_client.get(
        f"/api/v1/columns/{column_id}/cards",
    )
    assert len(list_again.json()) == 1


@pytest.mark.asyncio
async def test_move_card_between_columns(
    authed_client,
    seed_board_with_two_columns,
):
    source_column = seed_board_with_two_columns["column_a"]
    target_column = seed_board_with_two_columns["column_b"]

    create_response = await authed_client.post(
        f"/api/v1/columns/{source_column}/cards",
        json={"title": "Movable"},
    )
    card_id = create_response.json()["id"]

    move_response = await authed_client.post(
        f"/api/v1/cards/{card_id}/move",
        json={
            "target_column_id": target_column,
            "previous_card_id": None,
            "next_card_id": None,
        },
    )
    assert move_response.status_code == 200
    assert move_response.json()["column_id"] == target_column


@pytest.mark.asyncio
async def test_comment_with_mention_records_activity(
    authed_client,
    seed_board_with_column,
    mention_target_email,
):
    column_id = seed_board_with_column["column_id"]
    board_id = seed_board_with_column["board_id"]

    create_card = await authed_client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={"title": "Commentable"},
    )
    card_id = create_card.json()["id"]

    mention_handle = mention_target_email.split("@")[0]

    comment_response = await authed_client.post(
        f"/api/v1/cards/{card_id}/comments",
        json={"body": f"Hey @{mention_handle} please review"},
    )
    assert comment_response.status_code == 201

    comment = comment_response.json()
    assert len(comment["mentions"]) == 1

    activity_response = await authed_client.get(
        f"/api/v1/boards/{board_id}/activity",
    )
    assert activity_response.status_code == 200

    actions = [entry["action"] for entry in activity_response.json()]
    assert "comment.created" in actions
    assert "card.created" in actions
