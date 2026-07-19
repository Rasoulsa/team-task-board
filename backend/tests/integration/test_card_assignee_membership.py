import uuid

from httpx import AsyncClient
from pytest_mock import MockerFixture

PASSWORD = "Password123!"


async def register_and_login(
    client: AsyncClient,
    *,
    full_name: str,
) -> dict[str, str]:
    email = f"user-{uuid.uuid4().hex[:12]}@example.com"

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "full_name": full_name,
            "organization_name": (f"Organization {uuid.uuid4().hex[:8]}"),
        },
    )
    assert register_response.status_code in {200, 201}

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": PASSWORD,
        },
    )
    assert login_response.status_code == 200

    data = login_response.json()

    return {
        "email": email,
        "user_id": data["user"]["id"],
        "access_token": data["access_token"],
    }


def headers(user: dict[str, str]) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {user['access_token']}",
    }


async def create_card_resources(
    client: AsyncClient,
    owner: dict[str, str],
) -> dict[str, str]:
    organizations_response = await client.get(
        "/api/v1/organizations",
        headers=headers(owner),
    )
    assert organizations_response.status_code == 200

    organization_id = organizations_response.json()[0]["id"]

    project_response = await client.post(
        "/api/v1/projects",
        headers=headers(owner),
        json={
            "organization_id": organization_id,
            "name": "Assignee Project",
            "description": None,
        },
    )
    assert project_response.status_code == 201, project_response.text

    project_id = project_response.json()["id"]

    board_response = await client.post(
        f"/api/v1/projects/{project_id}/boards",
        headers=headers(owner),
        json={
            "name": "Assignee Board",
            "description": None,
        },
    )
    assert board_response.status_code == 201, board_response.text

    board_id = board_response.json()["id"]

    kanban_response = await client.get(
        f"/api/v1/boards/{board_id}/kanban",
        headers=headers(owner),
    )
    assert kanban_response.status_code == 200, kanban_response.text

    columns = kanban_response.json()["columns"]
    assert columns

    column_id = columns[0]["id"]

    card_response = await client.post(
        f"/api/v1/columns/{column_id}/cards",
        headers=headers(owner),
        json={
            "title": "Assignee membership test",
            "description": "Testing organization member assignment",
        },
    )
    assert card_response.status_code == 201, card_response.text

    return {
        "organization_id": organization_id,
        "board_id": board_id,
        "column_id": column_id,
        "card_id": card_response.json()["id"],
    }


async def test_organization_member_can_be_assigned(
    async_client: AsyncClient,
    mocker: MockerFixture,
) -> None:
    delay_mock = mocker.patch(
        "app.services.cards.notify_card_assigned.delay",
    )

    owner = await register_and_login(
        async_client,
        full_name="Assignment Owner",
    )
    member = await register_and_login(
        async_client,
        full_name="Assignment Member",
    )

    resources = await create_card_resources(
        async_client,
        owner,
    )

    invitation_response = await async_client.post(
        (f"/api/v1/organizations/{resources['organization_id']}/invitations"),
        headers=headers(owner),
        json={
            "email": member["email"],
            "role": "member",
        },
    )
    assert invitation_response.status_code == 201

    accept_response = await async_client.post(
        (f"/api/v1/invitations/{invitation_response.json()['token']}/accept"),
        headers=headers(member),
    )
    assert accept_response.status_code == 200

    assignment_response = await async_client.post(
        f"/api/v1/cards/{resources['card_id']}/assignees",
        headers=headers(owner),
        json={
            "user_id": member["user_id"],
        },
    )

    assert assignment_response.status_code == 201, assignment_response.text
    assert assignment_response.json()["user_id"] == member["user_id"]
    delay_mock.assert_called_once()


async def test_outside_user_cannot_be_assigned(
    async_client: AsyncClient,
) -> None:
    owner = await register_and_login(
        async_client,
        full_name="Assignment Owner",
    )
    outsider = await register_and_login(
        async_client,
        full_name="Organization Outsider",
    )

    resources = await create_card_resources(
        async_client,
        owner,
    )

    response = await async_client.post(
        f"/api/v1/cards/{resources['card_id']}/assignees",
        headers=headers(owner),
        json={
            "user_id": outsider["user_id"],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "The selected user is not a member of this card's organization"
    )
