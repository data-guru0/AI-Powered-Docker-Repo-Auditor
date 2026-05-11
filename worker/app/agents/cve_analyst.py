import json
import uuid
from typing import Any, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a CVE Analysis Agent specialized in container security.

Your task is to analyze raw CVE data from Trivy and AWS Inspector scans and produce structured,
actionable findings. For each CVE:

1. Assess actual exploitability — is the vulnerable binary in the runtime path?
2. Cross-reference EPSS scores for exploit probability
3. Check if it's in CISA KEV (Known Exploited Vulnerabilities)
4. Detect regressions — CVEs that appeared since the last scan
5. Prioritize by real risk, not just CVSS score
6. Provide the exact fix version

IMPORTANT: If the scan data contains no vulnerabilities, return an empty JSON array [].
Do NOT invent or hallucinate CVEs. Only report what is present in the scan data.

Respond ONLY with a JSON array of findings. Each finding must have:
- id, severity, category ("cve"), title, detail, evidence, impact, fix, effort, agent ("cve_analyst")
- cvssScore, epssScore, isInKEV, isRegression"""


class CVEState(TypedDict):
    trivy_data: dict
    inspector_data: dict
    previous_scan: Optional[dict]
    findings: list[dict]
    error: Optional[str]


def _extract_vulnerabilities(trivy_data: dict) -> list[dict]:
    vulns = []
    for result in trivy_data.get("Results", []):
        target = result.get("Target", "")
        for v in result.get("Vulnerabilities") or []:
            vulns.append({
                "id": v.get("VulnerabilityID", ""),
                "pkg": v.get("PkgName", ""),
                "installed": v.get("InstalledVersion", ""),
                "fixed": v.get("FixedVersion", ""),
                "severity": v.get("Severity", ""),
                "cvss": v.get("CVSS", {}).get("nvd", {}).get("V3Score") or v.get("CVSS", {}).get("ghsa", {}).get("V3Score", 0),
                "description": v.get("Description", "")[:200],
                "target": target,
            })
    return vulns


async def _analyze_node(state: CVEState) -> CVEState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0, timeout=90)

    vulns = _extract_vulnerabilities(state["trivy_data"])
    logger.info("CVE analyst received %d vulnerabilities from Trivy", len(vulns))
    trivy_summary = json.dumps(vulns, indent=2)[:40000]
    inspector_summary = json.dumps(state["inspector_data"], indent=2)[:4000]
    prev_cves = []
    if state.get("previous_scan"):
        prev_cves = [
            f.get("title", "")
            for f in state["previous_scan"].get("findings", [])
            if f.get("category") == "cve"
        ]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Trivy Results:
{trivy_summary}

Inspector Results:
{inspector_summary}

Previous scan CVEs (for regression detection):
{json.dumps(prev_cves)}

Analyze and return findings as JSON array."""
        ),
    ]

    try:
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        if "```" in content:
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else parts[0]
            if content.startswith("json"):
                content = content[4:]
        findings = json.loads(content.strip())
        for f in findings:
            f.setdefault("id", str(uuid.uuid4()))
            f.setdefault("agent", "cve_analyst")
            f.setdefault("category", "cve")
            if "severity" in f:
                f["severity"] = f["severity"].lower()
        return {**state, "findings": findings}
    except Exception as exc:
        logger.error("CVE analyst error: %s", exc)
        return {**state, "findings": [], "error": str(exc)}


def _build_graph() -> Any:
    graph = StateGraph(CVEState)
    graph.add_node("analyze", _analyze_node)
    graph.set_entry_point("analyze")
    graph.add_edge("analyze", END)
    return graph.compile()


_graph = _build_graph()


async def run_cve_analyst(
    trivy_data: dict,
    inspector_data: dict,
    previous_scan: Optional[dict] = None,
) -> list[dict]:
    has_trivy = bool(trivy_data.get("Results"))
    has_inspector = bool(inspector_data.get("findings") or inspector_data.get("Results"))
    if not has_trivy and not has_inspector:
        logger.info("No scan data available, skipping CVE analysis")
        return []
    result = await _graph.ainvoke(
        {
            "trivy_data": trivy_data,
            "inspector_data": inspector_data,
            "previous_scan": previous_scan,
            "findings": [],
            "error": None,
        }
    )
    return result["findings"]
