import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ping(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/ping")

    assert response.status_code == 200
    assert response.json() == {"message": "pong"}
