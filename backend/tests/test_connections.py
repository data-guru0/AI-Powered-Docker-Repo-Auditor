import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_get_connection_status(client, mock_dynamodb):
    mock_dynamodb.return_value.Table.return_value.get_item.return_value = {
        "Item": {"user_id": "test-user-123", "connections": []}
    }
    response = await client.get("/api/v1/connections/status")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_connect_dockerhub_invalid_credentials(client):
    with patch(
        "app.api.v1.connections.validate_dockerhub_credentials",
        return_value=False,
    ):
        response = await client.post(
            "/api/v1/connections/dockerhub",
            json={"username": "testuser", "accessToken": "invalid-token"},
        )
    assert response.status_code == 400
    assert "Invalid" in response.json()["detail"]


@pytest.mark.asyncio
async def test_connect_dockerhub_valid_credentials(client, mock_dynamodb, mock_secrets):
    mock_dynamodb.return_value.Table.return_value.get_item.return_value = {
        "Item": {"user_id": "test-user-123", "connections": []}
    }
    mock_dynamodb.return_value.Table.return_value.update_item.return_value = {}
    mock_secrets.return_value.create_secret.return_value = {}

    with patch(
        "app.api.v1.connections.validate_dockerhub_credentials",
        return_value=True,
    ):
        response = await client.post(
            "/api/v1/connections/dockerhub",
            json={"username": "testuser", "accessToken": "valid-token"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "dockerhub"
    assert data["status"] == "connected"
    assert data["username"] == "testuser"
