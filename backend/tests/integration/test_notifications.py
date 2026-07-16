from httpx import AsyncClient


async def test_unread_count_starts_at_zero(
    authed_client: AsyncClient,
) -> None:
    response = await authed_client.get(
        "/api/v1/notifications/unread-count",
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"unread_count": 0}
