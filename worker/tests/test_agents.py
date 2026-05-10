import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


@pytest.mark.asyncio
async def test_cve_analyst_returns_findings(sample_trivy_output):
    mock_response = MagicMock()
    mock_response.content = json.dumps([
        {
            "id": "test-cve-1",
            "severity": "critical",
            "category": "cve",
            "title": "CVE-2023-1234",
            "detail": "Buffer overflow in OpenSSL",
            "evidence": "openssl 3.0.0 installed",
            "impact": "Remote code execution possible",
            "fix": "Upgrade to openssl 3.0.8",
            "effort": "low",
            "agent": "cve_analyst",
            "cvssScore": 9.8,
            "epssScore": 0.8,
            "isInKEV": True,
            "isRegression": False,
        }
    ])

    with patch("app.agents.cve_analyst.ChatOpenAI") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm

        from app.agents.cve_analyst import run_cve_analyst
        findings = await run_cve_analyst(sample_trivy_output, {}, None)

    assert len(findings) > 0
    assert findings[0]["severity"] == "critical"
    assert findings[0]["agent"] == "cve_analyst"


@pytest.mark.asyncio
async def test_bloat_detective_returns_findings(sample_layer_data):
    mock_response = MagicMock()
    mock_response.content = json.dumps([
        {
            "id": "bloat-1",
            "severity": "medium",
            "category": "bloat",
            "title": "Dev tools in production image",
            "detail": "build-essential is a development package",
            "evidence": "Layer 1: 200MB RUN apt-get install -y build-essential",
            "impact": "200MB wasted in production image",
            "fix": "Use multi-stage build to separate build and runtime",
            "effort": "medium",
            "agent": "bloat_detective",
            "sizeImpact": 200_000_000,
            "isGhostFile": False,
        }
    ])

    with patch("app.agents.bloat_detective.ChatOpenAI") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm

        from app.agents.bloat_detective import run_bloat_detective
        findings = await run_bloat_detective(sample_layer_data, {})

    assert len(findings) > 0
    assert findings[0]["category"] == "bloat"


@pytest.mark.asyncio
async def test_risk_scorer_returns_scores():
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "scores": {
            "security": 30,
            "bloat": 55,
            "freshness": 70,
            "bestPractices": 60,
            "overall": "D",
        },
        "topActions": [
            {"rank": 1, "title": "Fix critical CVEs", "impact": "High", "effort": "low"}
        ],
        "executiveSummary": "This image has critical security issues that must be addressed.",
        "blocked": True,
        "scoreTrend": {},
    })

    with patch("app.agents.risk_scorer.ChatOpenAI") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm

        from app.agents.risk_scorer import run_risk_scorer
        result = await run_risk_scorer(
            [{"severity": "critical", "category": "cve"}],
            [],
            [],
            [],
            None,
        )

    assert result["scores"]["security"] == 30
    assert result["scores"]["overall"] == "D"
    assert result["blocked"] is True


def test_merge_findings():
    from app.processors.findings import merge_findings, deduplicate_findings
    list1 = [{"id": "a", "title": "CVE-1", "category": "cve"}]
    list2 = [{"id": "b", "title": "Bloat-1", "category": "bloat"}]
    list3 = [{"id": "a", "title": "CVE-1", "category": "cve"}]

    merged = merge_findings(list1, list2, list3)
    assert len(merged) == 3

    unique = deduplicate_findings(merged)
    assert len(unique) == 2


def test_normalize_severity():
    from app.processors.findings import normalize_severity
    assert normalize_severity("CRITICAL") == "critical"
    assert normalize_severity("HIGH") == "high"
    assert normalize_severity("UNKNOWN") == "informational"
    assert normalize_severity("NEGLIGIBLE") == "informational"
