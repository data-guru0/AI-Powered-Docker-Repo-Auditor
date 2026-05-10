import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_start_scan(client, mock_sqs):
    mock_sqs.return_value.send_message.return_value = {"MessageId": "test-msg-id"}

    with patch("app.services.ses.send_scan_started_email", new_callable=AsyncMock):
        response = await client.post(
            "/api/v1/scans",
            json={"repo_id": "myorg/myrepo"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["repoId"] == "myorg/myrepo"
    assert data["status"] == "queued"
    assert "jobId" in data


@pytest.mark.asyncio
async def test_get_scan_not_found(client, mock_dynamodb):
    mock_dynamodb.return_value.Table.return_value.get_item.return_value = {}

    response = await client.get("/api/v1/scans/nonexistent-scan-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_latest_scan_none(client, mock_dynamodb):
    mock_dynamodb.return_value.Table.return_value.query.return_value = {"Items": []}
    response = await client.get("/api/v1/scans/latest/myorg%2Fmyrepo")
    assert response.status_code == 200
    assert response.json() is None
