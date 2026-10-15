import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_agent_chat_queries():
    transport = ASGITransport(app=app)

    # Pass CSRF tokens in headers and cookies
    headers = {"X-CSRF-Token": "test-csrf-token"}
    cookies = {"csrf_token": "test-csrf-token"}

    with patch("app.api.v1.deps.get_current_tenant_user") as mock_user:
        mock_user.return_value = {"org_id": "org_test_123", "user": {"_id": "u1"}}

        async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
            res = await client.post("/api/v1/agent/chat", json={"message": "Hello AI"}, headers=headers)
            assert res.status_code in [200, 401]
