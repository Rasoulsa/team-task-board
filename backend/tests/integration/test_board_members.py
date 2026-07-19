import uuid

from httpx import AsyncClient

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


async def test_board_members_are_organization_members(
    async_client: AsyncClient,
) -> None:
    owner = await register_and_login(
        async_client,
        full_name="Board Owner",
    )
    member = await register_and_login(
        async_client,
        full_name="Board Member",
    )

    organizations_response = await async_client.get(
        "/api/v1/organizations",
        headers=headers(owner),
    )
    assert organizations_response.status_code == 200

    organization_id = organizations_response.json()[0]["id"]

    project_response = await async_client.post(
        "/api/v1/projects",
        headers=headers(owner),
        json={
            "organization_id": organization_id,
            "name": "Board Members Project",
            "description": None,
        },
    )
    assert project_response.status_code == 201, project_response.text

    project_id = project_response.json()["id"]

    board_response = await async_client.post(
        f"/api/v1/projects/{project_id}/boards",
        headers=headers(owner),
        json={
            "name": "Board Members Board",
            "description": None,
        },
    )
    assert board_response.status_code == 201, board_response.text

    board_id = board_response.json()["id"]

    invitation_response = await async_client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
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

    members_response = await async_client.get(
        f"/api/v1/boards/{board_id}/members",
        headers=headers(owner),
    )
    assert members_response.status_code == 200, members_response.text

    members = members_response.json()
    user_ids = {item["user_id"] for item in members}

    assert owner["user_id"] in user_ids
    assert member["user_id"] in user_ids

    member_item = next(item for item in members if item["user_id"] == member["user_id"])

    assert member_item["full_name"] == "Board Member"
    assert member_item["email"] == member["email"]
    assert member_item["role"] == "member"
