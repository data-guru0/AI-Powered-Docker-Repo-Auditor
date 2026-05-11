import json
import uuid
from typing import Any, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a CIS Docker Benchmark Compliance Agent.

Your task is to audit a container image against the CIS Docker Benchmark v1.6 rules.

For EACH rule below, produce one finding — either PASSING or FAILING:

CIS 4.1  - Create a non-root user (USER directive present and not root/0)
CIS 4.2  - Use trusted base images (known official registry, not untagged/unknown)
CIS 4.3  - Do not install unnecessary packages (dev tools, build deps in runtime image)
CIS 4.6  - Add HEALTHCHECK instruction
CIS 4.7  - Do not use update instructions alone (apt-get update must be paired with install in same RUN)
CIS 4.9  - Use COPY instead of ADD (ADD with local files should be COPY)
CIS 4.10 - Do not store secrets in Dockerfiles (ENV with keys, passwords, tokens, secrets)
CIS 5.8  - Do not expose privileged ports (< 1024) or sensitive service ports (22, 3306, 5432, 27017, 6379)

Severity rules:
- PASSING → severity must be "informational"
- FAILING → use "critical" for secrets/root-user, "high" for privileged ports/no-healthcheck, "medium" for others

Respond ONLY with a JSON array. Each finding must have:
- id, severity, category ("compliance"), title, detail, evidence, impact, fix, effort, agent ("compliance_checker")
- cisRule (e.g. "CIS 4.1"), status ("pass" or "fail")"""


class ComplianceState(TypedDict):
    manifest: dict
    trivy_data: dict
    findings: list[dict]
    error: Optional[str]


async def _check_node(state: ComplianceState) -> ComplianceState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0, timeout=90)

    manifest_summary = json.dumps(state["manifest"], indent=2)[:6000]
    trivy_summary = json.dumps(state["trivy_data"], indent=2)[:3000]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Image Manifest (contains Dockerfile history, config, ENV, EXPOSE, USER):
{manifest_summary}

Trivy Scan Data (for additional context):
{trivy_summary}

Check all 8 CIS rules and return one finding per rule as a JSON array.
Base your findings ONLY on what is present in the manifest data. Do NOT invent findings."""
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
            f.setdefault("agent", "compliance_checker")
            f.setdefault("category", "compliance")
        return {**state, "findings": findings}
    except Exception as exc:
        logger.error("Compliance checker error: %s", exc)
        return {**state, "findings": [], "error": str(exc)}


def _build_graph() -> Any:
    graph = StateGraph(ComplianceState)
    graph.add_node("check", _check_node)
    graph.set_entry_point("check")
    graph.add_edge("check", END)
    return graph.compile()


_graph = _build_graph()


async def run_compliance_checker(
    manifest: dict,
    trivy_data: dict,
) -> list[dict]:
    result = await _graph.ainvoke(
        {
            "manifest": manifest,
            "trivy_data": trivy_data,
            "findings": [],
            "error": None,
        }
    )
    return result["findings"]
