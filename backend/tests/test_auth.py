import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import patch, AsyncMock

from httpx import ASGITransport

@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)

    with patch("app.main.db.command", new_callable=AsyncMock) as mock_command:
        mock_command.return_value = {"ok": 1}
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
