import json
import uuid
from typing import Any, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Dockerfile Optimizer Agent.

You receive:
1. The original reconstructed Dockerfile
2. CVE findings from the CVE Analysis Agent
3. Bloat findings from the Bloat Detective Agent
4. Base image recommendations from the Base Image Strategist Agent

Your task is to produce:
1. A fully rewritten, optimized Dockerfile with:
   - Multi-stage builds where applicable
   - Layer ordering optimized for cache efficiency
   - Package caches cleaned in same RUN instruction
   - Dev tools and test fixtures removed
   - Base image pinned to digest
   - All CVE fixes applied
2. A structured list of every change made with:
   - lineNumber (in the optimized Dockerfile)
   - category: "security" | "bloat" | "cache" | "best-practice"
   - what: description of the change
   - why: reason for the change
   - estimatedSavings: estimated size or security improvement

Return JSON with keys "original", "optimized", "changes"."""


class DockerfileState(TypedDict):
    manifest: dict
    cve_findings: list[dict]
    bloat_findings: list[dict]
    base_image_findings: list[dict]
    result: dict
    error: Optional[str]


async def _optimize_node(state: DockerfileState) -> DockerfileState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    manifest_str = json.dumps(state["manifest"], indent=2)[:3000]
    cve_str = json.dumps(state["cve_findings"][:10], indent=2)[:3000]
    bloat_str = json.dumps(state["bloat_findings"][:10], indent=2)[:3000]
    base_str = json.dumps(state["base_image_findings"][:5], indent=2)[:2000]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Image Manifest (contains original Dockerfile layers):
{manifest_str}

CVE Findings:
{cve_str}

Bloat Findings:
{bloat_str}

Base Image Findings:
{base_str}

Generate the optimized Dockerfile and changes. Return JSON with "original", "optimized", "changes"."""
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
        for change in result.get("changes", []):
            change.setdefault("id", str(uuid.uuid4()))
        return {**state, "result": result}
    except Exception as exc:
        logger.error("Dockerfile optimizer error: %s", exc)
        return {
            **state,
            "result": {"original": "", "optimized": "", "changes": []},
            "error": str(exc),
        }


def _build_graph() -> Any:
    graph = StateGraph(DockerfileState)
    graph.add_node("optimize", _optimize_node)
    graph.set_entry_point("optimize")
    graph.add_edge("optimize", END)
    return graph.compile()


_graph = _build_graph()


async def run_dockerfile_optimizer(
    manifest: dict,
    cve_findings: list[dict],
    bloat_findings: list[dict],
    base_image_findings: list[dict],
) -> dict:
    result = await _graph.ainvoke(
        {
            "manifest": manifest,
            "cve_findings": cve_findings,
            "bloat_findings": bloat_findings,
            "base_image_findings": base_image_findings,
            "result": {},
            "error": None,
        }
    )
    return result["result"]
