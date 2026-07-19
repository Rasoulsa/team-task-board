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
            "organization_name": (f"{full_name} Organization {uuid.uuid4().hex[:8]}"),
        },
    )
    assert register_response.status_code in {200, 201}, register_response.text

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": PASSWORD,
        },
    )
    assert login_response.status_code == 200, login_response.text

    data = login_response.json()

    return {
        "email": email,
        "user_id": data["user"]["id"],
        "access_token": data["access_token"],
    }


def auth_headers(user: dict[str, str]) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {user['access_token']}",
    }


async def get_first_organization_id(
    client: AsyncClient,
    user: dict[str, str],
) -> str:
    response = await client.get(
        "/api/v1/organizations",
        headers=auth_headers(user),
    )
    assert response.status_code == 200, response.text

    organizations = response.json()
    assert organizations

    return organizations[0]["id"]


async def test_owner_invites_user_and_user_accepts(
    async_client: AsyncClient,
) -> None:
    owner = await register_and_login(
        async_client,
        full_name="Invitation Owner",
    )
    invited_user = await register_and_login(
        async_client,
        full_name="Invited Member",
    )

    organization_id = await get_first_organization_id(
        async_client,
        owner,
    )

    invitation_response = await async_client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        headers=auth_headers(owner),
        json={
            "email": invited_user["email"],
            "role": "member",
        },
    )
    assert invitation_response.status_code == 201, invitation_response.text

    invitation = invitation_response.json()

    assert invitation["email"] == invited_user["email"]
    assert invitation["role"] == "member"
    assert invitation["status"] == "pending"
    assert invitation["token"]

    accept_response = await async_client.post(
        f"/api/v1/invitations/{invitation['token']}/accept",
        headers=auth_headers(invited_user),
    )
    assert accept_response.status_code == 200, accept_response.text

    membership = accept_response.json()

    assert membership["organization_id"] == organization_id
    assert membership["user_id"] == invited_user["user_id"]
    assert membership["role"] == "member"

    members_response = await async_client.get(
        f"/api/v1/organizations/{organization_id}/members",
        headers=auth_headers(owner),
    )
    assert members_response.status_code == 200, members_response.text

    member_user_ids = {member["user_id"] for member in members_response.json()}

    assert owner["user_id"] in member_user_ids
    assert invited_user["user_id"] in member_user_ids


async def test_wrong_user_cannot_accept_invitation(
    async_client: AsyncClient,
) -> None:
    owner = await register_and_login(
        async_client,
        full_name="Invitation Owner",
    )
    invited_user = await register_and_login(
        async_client,
        full_name="Correct Invitee",
    )
    wrong_user = await register_and_login(
        async_client,
        full_name="Wrong Invitee",
    )

    organization_id = await get_first_organization_id(
        async_client,
        owner,
    )

    invitation_response = await async_client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        headers=auth_headers(owner),
        json={
            "email": invited_user["email"],
            "role": "member",
        },
    )
    assert invitation_response.status_code == 201

    token = invitation_response.json()["token"]

    response = await async_client.post(
        f"/api/v1/invitations/{token}/accept",
        headers=auth_headers(wrong_user),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == ("This invitation belongs to another user")


async def test_invitation_cannot_be_accepted_twice(
    async_client: AsyncClient,
) -> None:
    owner = await register_and_login(
        async_client,
        full_name="Invitation Owner",
    )
    invited_user = await register_and_login(
        async_client,
        full_name="Invited Member",
    )

    organization_id = await get_first_organization_id(
        async_client,
        owner,
    )

    invitation_response = await async_client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        headers=auth_headers(owner),
        json={
            "email": invited_user["email"],
            "role": "member",
        },
    )
    assert invitation_response.status_code == 201

    token = invitation_response.json()["token"]

    first_response = await async_client.post(
        f"/api/v1/invitations/{token}/accept",
        headers=auth_headers(invited_user),
    )
    assert first_response.status_code == 200

    second_response = await async_client.post(
        f"/api/v1/invitations/{token}/accept",
        headers=auth_headers(invited_user),
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == ("Invitation has already been accepted")


async def test_duplicate_pending_invitation_is_rejected(
    async_client: AsyncClient,
) -> None:
    owner = await register_and_login(
        async_client,
        full_name="Invitation Owner",
    )
    invited_user = await register_and_login(
        async_client,
        full_name="Invited Member",
    )

    organization_id = await get_first_organization_id(
        async_client,
        owner,
    )

    url = f"/api/v1/organizations/{organization_id}/invitations"
    payload = {
        "email": invited_user["email"],
        "role": "member",
    }

    first_response = await async_client.post(
        url,
        headers=auth_headers(owner),
        json=payload,
    )
    assert first_response.status_code == 201

    second_response = await async_client.post(
        url,
        headers=auth_headers(owner),
        json=payload,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A pending invitation already exists for this email"
    )


async def test_existing_member_cannot_be_invited_again(
    async_client: AsyncClient,
) -> None:
    owner = await register_and_login(
        async_client,
        full_name="Invitation Owner",
    )
    member = await register_and_login(
        async_client,
        full_name="Invited Member",
    )

    organization_id = await get_first_organization_id(
        async_client,
        owner,
    )

    invitation_response = await async_client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        headers=auth_headers(owner),
        json={
            "email": member["email"],
            "role": "member",
        },
    )
    assert invitation_response.status_code == 201

    accept_response = await async_client.post(
        (f"/api/v1/invitations/{invitation_response.json()['token']}/accept"),
        headers=auth_headers(member),
    )
    assert accept_response.status_code == 200

    second_invitation_response = await async_client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        headers=auth_headers(owner),
        json={
            "email": member["email"],
            "role": "member",
        },
    )

    assert second_invitation_response.status_code == 409
    assert second_invitation_response.json()["detail"] == (
        "This user is already a member of the organization"
    )


async def test_member_cannot_invite_another_user(
    async_client: AsyncClient,
) -> None:
    owner = await register_and_login(
        async_client,
        full_name="Invitation Owner",
    )
    member = await register_and_login(
        async_client,
        full_name="Organization Member",
    )
    third_user = await register_and_login(
        async_client,
        full_name="Third User",
    )

    organization_id = await get_first_organization_id(
        async_client,
        owner,
    )

    invitation_response = await async_client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        headers=auth_headers(owner),
        json={
            "email": member["email"],
            "role": "member",
        },
    )
    assert invitation_response.status_code == 201

    accept_response = await async_client.post(
        (f"/api/v1/invitations/{invitation_response.json()['token']}/accept"),
        headers=auth_headers(member),
    )
    assert accept_response.status_code == 200

    response = await async_client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        headers=auth_headers(member),
        json={
            "email": third_user["email"],
            "role": "member",
        },
    )

    assert response.status_code == 403


async def test_owner_role_cannot_be_assigned_by_invitation(
    async_client: AsyncClient,
) -> None:
    owner = await register_and_login(
        async_client,
        full_name="Invitation Owner",
    )
    invited_user = await register_and_login(
        async_client,
        full_name="Invited Owner",
    )

    organization_id = await get_first_organization_id(
        async_client,
        owner,
    )

    response = await async_client.post(
        f"/api/v1/organizations/{organization_id}/invitations",
        headers=auth_headers(owner),
        json={
            "email": invited_user["email"],
            "role": "owner",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Cannot invite a user with the owner role")
