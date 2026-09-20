import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from app.main import app

from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_health_check():
    with patch("app.main.db.command", new_callable=AsyncMock) as mock_command:
        mock_command.return_value = {"ok": 1}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"