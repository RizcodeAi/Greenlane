import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.config import settings


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """Create an httpx AsyncClient with the FastAPI test app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db():
    """Provide a test database connection."""
    from app.core.database import client as mongo_client, db as database
    yield database
    # Teardown: close the client connection after tests
    mongo_client.close()