import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.v1.deps import get_current_tenant_user

@pytest.mark.asyncio
async def test_agent_chat_queries():
    transport = ASGITransport(app=app)

    async def mock_get_current_tenant_user():
        return {
            "org_id": "org_test_123",
            "user": {"_id": "u1", "email": "test@greenlane.io", "role": "Fleet Manager"}
        }

    app.dependency_overrides[get_current_tenant_user] = mock_get_current_tenant_user

    headers = {"X-CSRF-Token": "test-csrf-token"}
    cookies = {"csrf_token": "test-csrf-token"}

    try:
        async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
            res = await client.post("/api/v1/agent/chat", json={"message": "Hello AI"}, headers=headers)
            assert res.status_code == 200
            data = res.json()
            assert "reply" in data
            assert isinstance(data["actions_taken"], list)
    finally:
        app.dependency_overrides.clear()
