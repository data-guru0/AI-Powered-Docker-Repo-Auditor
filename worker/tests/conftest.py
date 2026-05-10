import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_openai():
    with patch("langchain_openai.ChatOpenAI") as mock:
        instance = MagicMock()
        instance.ainvoke = AsyncMock(
            return_value=MagicMock(
                content='[{"id": "test-1", "severity": "high", "category": "cve", "title": "Test CVE", "detail": "Test detail", "evidence": "Test evidence", "impact": "Test impact", "fix": "Test fix", "effort": "medium", "agent": "cve_analyst"}]'
            )
        )
        mock.return_value = instance
        yield mock


@pytest.fixture
def sample_trivy_output():
    return {
        "Results": [
            {
                "Target": "myimage:latest (ubuntu 22.04)",
                "Type": "ubuntu",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2023-1234",
                        "PkgName": "openssl",
                        "InstalledVersion": "3.0.0",
                        "FixedVersion": "3.0.8",
                        "Severity": "CRITICAL",
                        "Description": "Buffer overflow in OpenSSL",
                        "CVSS": {"nvd": {"V3Score": 9.8}},
                    }
                ],
            }
        ]
    }


@pytest.fixture
def sample_layer_data():
    return [
        {
            "index": 0,
            "digest": "sha256:abc123",
            "size": 50_000_000,
            "command": "FROM ubuntu:22.04",
            "createdAt": "2024-01-01T00:00:00Z",
        },
        {
            "index": 1,
            "digest": "sha256:def456",
            "size": 200_000_000,
            "command": "RUN apt-get install -y build-essential python3-dev",
            "createdAt": "2024-01-01T00:01:00Z",
        },
    ]
