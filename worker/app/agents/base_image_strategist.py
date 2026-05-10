import json
import uuid
from typing import Any, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Base Image Strategist Agent for container images.

Your task is to analyze the current base image and recommend improvements.

For the current base image:
1. Identify the exact image and digest
2. Check if it uses a mutable tag like "latest"
3. Assess if it's EOL or approaching EOL
4. Suggest migration paths toward distroless or scratch
5. For each migration option, analyze: size delta, compatibility, security improvement, tradeoffs
6. Warn about any concerns

Respond with TWO things:
1. A JSON object with analysis: currentImage, currentDigest, currentVersion, latestVersion, isEOL, eolDate, hasMutableTag, migrationOptions
2. A JSON array of findings with: id, severity, category ("base_image"), title, detail, evidence, impact, fix, effort, agent ("base_image_strategist")

Return a JSON object with keys "analysis" and "findings"."""


class BaseImageState(TypedDict):
    manifest: dict
    analysis: dict
    findings: list[dict]
    error: Optional[str]


async def _strategize_node(state: BaseImageState) -> BaseImageState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0, timeout=90)

    manifest_summary = json.dumps(state["manifest"], indent=2)[:6000]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Image Manifest:
{manifest_summary}

Analyze the base image and return JSON with "analysis" and "findings" keys."""
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
        analysis = result.get("analysis", {})
        findings = result.get("findings", [])
        for f in findings:
            f.setdefault("id", str(uuid.uuid4()))
            f.setdefault("agent", "base_image_strategist")
            f.setdefault("category", "base_image")
        return {**state, "analysis": analysis, "findings": findings}
    except Exception as exc:
        logger.error("Base image strategist error: %s", exc)
        return {**state, "analysis": {}, "findings": [], "error": str(exc)}


def _build_graph() -> Any:
    graph = StateGraph(BaseImageState)
    graph.add_node("strategize", _strategize_node)
    graph.set_entry_point("strategize")
    graph.add_edge("strategize", END)
    return graph.compile()


_graph = _build_graph()


async def run_base_image_strategist(manifest: dict) -> list[dict]:
    result = await _graph.ainvoke(
        {
            "manifest": manifest,
            "analysis": {},
            "findings": [],
            "error": None,
        }
    )
    return result["findings"]
