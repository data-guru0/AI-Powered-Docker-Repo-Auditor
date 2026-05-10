import json
from typing import Any, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Risk Scorer Agent for container image security.

You receive all specialist agent outputs and must produce:
1. Four scores (0-100): Security, Bloat, Freshness, Best Practices
2. An overall grade: A (90+), B (80+), C (70+), D (60+), F (<60)
3. Top 5 prioritized actions by impact
4. Score comparison to previous scan (trend analysis)
5. A plain English executive summary (2-3 sentences)
6. A blocked flag if the image violates critical thresholds (critical CVEs > 5 OR security score < 30)

Return JSON with:
{
  "scores": { "security": int, "bloat": int, "freshness": int, "bestPractices": int, "overall": string },
  "topActions": [ { "rank": int, "title": str, "impact": str, "effort": str } ],
  "executiveSummary": str,
  "blocked": bool,
  "scoreTrend": { "security": int, "bloat": int, "freshness": int, "bestPractices": int }
}"""


class RiskState(TypedDict):
    cve_findings: list[dict]
    bloat_findings: list[dict]
    base_image_findings: list[dict]
    all_findings: list[dict]
    previous_scan: Optional[dict]
    result: dict
    error: Optional[str]


async def _score_node(state: RiskState) -> RiskState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    cve_critical = sum(
        1 for f in state["cve_findings"] if f.get("severity") == "critical"
    )
    cve_high = sum(1 for f in state["cve_findings"] if f.get("severity") == "high")
    total_bloat = sum(f.get("sizeImpact", 0) for f in state["bloat_findings"])

    prev_scores = {}
    if state.get("previous_scan"):
        prev_scores = state["previous_scan"].get("scores", {})

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""CVE Findings Summary:
- Critical: {cve_critical}
- High: {cve_high}
- Total CVE findings: {len(state["cve_findings"])}

Bloat Findings Summary:
- Total bloat findings: {len(state["bloat_findings"])}
- Total size impact: {total_bloat} bytes

Base Image Findings:
{json.dumps(state["base_image_findings"][:5], indent=2)[:2000]}

All Findings Count: {len(state["all_findings"])}

Previous Scan Scores (for trend):
{json.dumps(prev_scores)}

Calculate risk scores and return JSON."""
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
        result = json.loads(content.strip())
        return {**state, "result": result}
    except Exception as exc:
        logger.error("Risk scorer error: %s", exc)
        return {
            **state,
            "result": {
                "scores": {
                    "security": 50, "bloat": 50, "freshness": 50,
                    "bestPractices": 50, "overall": "C"
                },
                "topActions": [],
                "executiveSummary": "Risk scoring failed due to an error.",
                "blocked": False,
                "scoreTrend": {},
            },
            "error": str(exc),
        }


def _build_graph() -> Any:
    graph = StateGraph(RiskState)
    graph.add_node("score", _score_node)
    graph.set_entry_point("score")
    graph.add_edge("score", END)
    return graph.compile()


_graph = _build_graph()


async def run_risk_scorer(
    cve_findings: list[dict],
    bloat_findings: list[dict],
    base_image_findings: list[dict],
    all_findings: list[dict],
    previous_scan: Optional[dict] = None,
) -> dict:
    result = await _graph.ainvoke(
        {
            "cve_findings": cve_findings,
            "bloat_findings": bloat_findings,
            "base_image_findings": base_image_findings,
            "all_findings": all_findings,
            "previous_scan": previous_scan,
            "result": {},
            "error": None,
        }
    )
    return result["result"]
