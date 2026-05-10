import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from app.main import app
from app.core.auth import get_current_user


@pytest.fixture
def mock_user():
    return {"user_id": "test-user-123", "email": "test@example.com"}


@pytest_asyncio.fixture
async def client(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def mock_dynamodb():
    with patch("app.services.dynamodb.get_dynamodb_resource") as mock:
        yield mock


@pytest.fixture
def mock_secrets():
    with patch("app.services.secrets.get_secrets_client") as mock:
        yield mock


@pytest.fixture
def mock_sqs():
    with patch("app.services.queue.get_sqs_client") as mock:
        yield mock
