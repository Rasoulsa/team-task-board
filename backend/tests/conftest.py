import uuid
from collections.abc import AsyncIterator
from typing import TypedDict

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import app


class AuthenticatedUser(TypedDict):
    client: AsyncClient
    user_id: str
    email: str
    access_token: str


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncIterator[AsyncClient]:
    """HTTP client with FastAPI startup and shutdown events enabled."""

    async with LifespanManager(app):
        transport = ASGITransport(app=app)

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as test_client:
            yield test_client


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clear_auth_rate_limits(async_client: AsyncClient) -> AsyncIterator[None]:
    """Keep auth rate-limit state isolated between integration tests.

    ASGITransport uses one simulated client address for all tests, while Redis
    retains counters across requests. Clear only auth rate-limit keys, not the
    whole Redis database.
    """
    redis = app.state.redis

    keys = [key async for key in redis.scan_iter(match="rate-limit:auth:*")]

    if keys:
        await redis.delete(*keys)

    yield

    keys = [key async for key in redis.scan_iter(match="rate-limit:auth:*")]

    if keys:
        await redis.delete(*keys)


@pytest_asyncio.fixture(scope="function")
async def authenticated_user(
    async_client: AsyncClient,
) -> AuthenticatedUser:
    """Register and authenticate a user and expose its identity."""

    email = f"test-user-{uuid.uuid4().hex[:12]}@example.com"
    password = "Password123!"

    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
            "organization_name": f"Test Organization {uuid.uuid4().hex[:8]}",
        },
    )
    assert register_response.status_code in {200, 201}, register_response.text

    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200, login_response.text

    access_token = login_response.json()["access_token"]

    async_client.headers.update(
        {"Authorization": f"Bearer {access_token}"},
    )

    me_response = await async_client.get("/api/v1/auth/me")
    assert me_response.status_code == 200, me_response.text

    user_id = me_response.json()["id"]

    return {
        "client": async_client,
        "user_id": user_id,
        "email": email,
        "access_token": access_token,
    }


@pytest_asyncio.fixture(scope="function")
async def authed_client(
    authenticated_user: AuthenticatedUser,
) -> AsyncClient:
    """Return the HTTP client authenticated by authenticated_user."""

    return authenticated_user["client"]


@pytest_asyncio.fixture(scope="function")
async def seed_org_project(authed_client: AsyncClient) -> dict[str, str]:
    """Use the organization created during registration and create a project."""

    organizations_response = await authed_client.get("/api/v1/organizations")
    assert organizations_response.status_code == 200, organizations_response.text

    organizations = organizations_response.json()
    assert organizations, "The registered test user should belong to an organization"

    organization_id = organizations[0]["id"]

    project_response = await authed_client.post(
        "/api/v1/projects",
        json={
            "organization_id": organization_id,
            "name": f"Cards Test Project {uuid.uuid4().hex[:8]}",
            "description": "Project used by card integration tests",
        },
    )
    assert project_response.status_code == 201, project_response.text

    return {
        "organization_id": organization_id,
        "project_id": project_response.json()["id"],
    }


@pytest_asyncio.fixture(scope="function")
async def seed_board_with_column(
    authed_client: AsyncClient,
    seed_org_project: dict[str, str],
) -> dict[str, str]:
    """Create a board and one column for the authenticated organization."""

    project_id = seed_org_project["project_id"]

    board_response = await authed_client.post(
        f"/api/v1/projects/{project_id}/boards",
        json={"name": "Board A", "description": None},
    )
    assert board_response.status_code == 201, board_response.text

    board_id = board_response.json()["id"]

    column_response = await authed_client.post(
        f"/api/v1/boards/{board_id}/columns",
        json={"name": "Todo"},
    )
    assert column_response.status_code == 201, column_response.text

    column_id = column_response.json()["id"]

    return {"board_id": board_id, "column_id": column_id}


@pytest_asyncio.fixture(scope="function")
async def seed_board_with_two_columns(
    authed_client: AsyncClient,
    seed_org_project: dict[str, str],
) -> dict[str, str]:
    """Create a board containing Todo and Done columns."""

    project_id = seed_org_project["project_id"]

    board_response = await authed_client.post(
        f"/api/v1/projects/{project_id}/boards",
        json={"name": "Board B", "description": None},
    )
    assert board_response.status_code == 201, board_response.text

    board_id = board_response.json()["id"]

    column_a_response = await authed_client.post(
        f"/api/v1/boards/{board_id}/columns",
        json={"name": "Todo"},
    )
    assert column_a_response.status_code == 201, column_a_response.text

    column_b_response = await authed_client.post(
        f"/api/v1/boards/{board_id}/columns",
        json={"name": "Done"},
    )
    assert column_b_response.status_code == 201, column_b_response.text

    return {
        "board_id": board_id,
        "column_a": column_a_response.json()["id"],
        "column_b": column_b_response.json()["id"],
    }


@pytest_asyncio.fixture(scope="function")
async def mention_target_email(authed_client: AsyncClient) -> str:
    """Register a second user whose email handle can be mentioned."""

    email = f"mention-{uuid.uuid4().hex[:10]}@example.com"

    response = await authed_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Mention Target",
            "organization_name": f"Mention Org {uuid.uuid4().hex[:8]}",
        },
    )
    assert response.status_code in {200, 201}, response.text

    return email
