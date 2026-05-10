import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_list_repos_no_credentials(client):
    with patch(
        "app.api.v1.repositories.list_dockerhub_repos",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = await client.get("/api/v1/repositories?registry_type=dockerhub")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_ecr_repos(client):
    from app.models.registry import Repository, RegistryType
    mock_repo = Repository(
        id="ecr-myrepo",
        name="myrepo",
        registryType=RegistryType.ECR,
        imageCount=5,
        lastPushed="2024-01-01T00:00:00Z",
        totalSize=500000000,
    )
    with patch(
        "app.api.v1.repositories.list_ecr_repos",
        new_callable=AsyncMock,
        return_value=[mock_repo],
    ):
        response = await client.get("/api/v1/repositories?registry_type=ecr")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "myrepo"


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
