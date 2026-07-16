from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_comment_mention_enqueues_notification(
    authed_client: AsyncClient,
    seed_board_with_column: dict[str, str],
    mention_target_email: str,
    mocker: MockerFixture,
) -> None:
    delay_mock = mocker.patch(
        "app.services.comments.notify_card_mentioned.delay",
    )

    column_id = seed_board_with_column["column_id"]
    board_id = seed_board_with_column["board_id"]

    card_response = await authed_client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={"title": "Discuss release", "description": None},
    )
    assert card_response.status_code == 201, card_response.text
    card_id = card_response.json()["id"]
    card_title = card_response.json()["title"]

    handle = mention_target_email.split("@")[0]
    comment_response = await authed_client.post(
        f"/api/v1/cards/{card_id}/comments",
        json={"body": f"Hey @{handle} please review"},
    )
    assert comment_response.status_code == 201, comment_response.text

    delay_mock.assert_called_once()
    _, kwargs = delay_mock.call_args
    assert kwargs["author_name"] == "Test User"
    assert kwargs["card_id"] == card_id
    assert kwargs["card_title"] == card_title
    assert kwargs["board_id"] == board_id
    assert "user_id" in kwargs


@pytest.mark.asyncio
async def test_self_mention_does_not_enqueue(
    authed_client: AsyncClient,
    authenticated_user: dict[str, Any],
    seed_board_with_column: dict[str, str],
    mocker: MockerFixture,
) -> None:
    delay_mock = mocker.patch(
        "app.services.comments.notify_card_mentioned.delay",
    )

    column_id = seed_board_with_column["column_id"]
    self_handle = authenticated_user["email"].split("@")[0]

    card_response = await authed_client.post(
        f"/api/v1/columns/{column_id}/cards",
        json={"title": "Solo task", "description": None},
    )
    assert card_response.status_code == 201, card_response.text
    card_id = card_response.json()["id"]

    comment_response = await authed_client.post(
        f"/api/v1/cards/{card_id}/comments",
        json={"body": f"Note to @{self_handle}"},
    )
    assert comment_response.status_code == 201, comment_response.text

    delay_mock.assert_not_called()
