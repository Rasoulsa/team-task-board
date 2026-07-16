from __future__ import annotations

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from pytest_mock import MockerFixture


async def _register_second_user(client: AsyncClient) -> dict[str, str]:
    """Register a second user (separate org) and return id + email.

    add_assignee does not validate org membership of the target, only
    that the user row exists (FK card_assignees.user_id -> users.id).
    """
    email = f"assignee-{uuid.uuid4().hex[:10]}@example.com"
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Assignee User",
            "organization_name": f"Assignee Org {uuid.uuid4().hex[:8]}",
        },
    )
    assert register.status_code in {200, 201}, register.text
    return {"email": email, "user_id": register.json()["user"]["id"]}


@pytest.mark.asyncio
async def test_assigning_card_to_other_user_enqueues_notification(
    authed_client: AsyncClient,
    seed_board_with_column: dict[str, str],
    mocker: MockerFixture,
) -> None:
    delay_mock = mocker.patch(
        "app.services.cards.notify_card_assigned.delay",
    )

    column_id = seed_board_with_column["column_id"]
    board_id = seed_board_with_column["board_id"]

    card_response = await authed_client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={"title": "Ship it", "description": None},
    )
    assert card_response.status_code == 201, card_response.text
    card_id = card_response.json()["id"]
    card_title = card_response.json()["title"]

    second = await _register_second_user(authed_client)

    response = await authed_client.post(
        f"/api/v1/cards/{card_id}/assignees",
        json={"user_id": second["user_id"]},
    )
    assert response.status_code == 201, response.text

    delay_mock.assert_called_once_with(
        user_id=second["user_id"],
        assigner_name="Test User",
        card_id=card_id,
        card_title=card_title,
        board_id=board_id,
    )


@pytest.mark.asyncio
async def test_self_assign_does_not_enqueue(
    authed_client: AsyncClient,
    authenticated_user: dict[str, Any],
    seed_board_with_column: dict[str, str],
    mocker: MockerFixture,
) -> None:
    delay_mock = mocker.patch(
        "app.services.cards.notify_card_assigned.delay",
    )

    column_id = seed_board_with_column["column_id"]
    self_id = authenticated_user["user_id"]

    card_response = await authed_client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={"title": "My own task", "description": None},
    )
    assert card_response.status_code == 201, card_response.text
    card_id = card_response.json()["id"]

    response = await authed_client.post(
        f"/api/v1/cards/{card_id}/assignees",
        json={"user_id": self_id},
    )
    assert response.status_code == 201, response.text

    delay_mock.assert_not_called()
