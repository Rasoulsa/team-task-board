import pytest


@pytest.mark.asyncio
async def test_ping(client):
    resp = await client.get("/api/v1/ping")
    assert resp.status_code == 200
    assert resp.json() == {"message": "pong"}
