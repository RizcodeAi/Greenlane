import pytest
from httpx import AsyncClient
from app.main import app

from httpx import ASGITransport

from unittest.mock import patch

from unittest.mock import AsyncMock

@pytest.mark.asyncio
@patch("app.main.db.command", new_callable=AsyncMock)
async def test_health_check(mock_command):
    mock_command.return_value = {"ok": 1}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"