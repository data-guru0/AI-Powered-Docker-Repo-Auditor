import json
import uuid
from typing import Any, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Bloat Detective Agent for container images.

Your task is to analyze Docker image layer data and identify sources of unnecessary bloat.

For each bloat source:
1. Identify the root cause — which RUN or COPY instruction caused it
2. Detect ghost files — added then deleted across layers
3. Find package manager caches, dev tools in prod, test fixtures, build artifacts
4. Calculate the size impact
5. Provide an exact fix

IMPORTANT: Only report bloat that is actually visible in the layer data provided.
If the layer data is empty or minimal, return an empty JSON array [].
Do NOT invent findings.

Respond ONLY with a JSON array. Each item must have:
- id, severity, category ("bloat"), title, detail, evidence, impact, fix, effort, agent ("bloat_detective")
- layerDigest, layerCommand, layerIndex, sizeImpact, isGhostFile"""


class BloatState(TypedDict):
    layer_data: list[dict]
    manifest: dict
    findings: list[dict]
    error: Optional[str]


async def _detect_bloat_node(state: BloatState) -> BloatState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0, timeout=90)

    layers_summary = json.dumps(state["layer_data"], indent=2)[:8000]
    manifest_summary = json.dumps(state["manifest"], indent=2)[:3000]

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Layer Data:
{layers_summary}

Image Manifest:
{manifest_summary}

Identify all bloat sources and return findings as JSON array."""
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
            f.setdefault("agent", "bloat_detective")
            f.setdefault("category", "bloat")
        return {**state, "findings": findings}
    except Exception as exc:
        logger.error("Bloat detective error: %s", exc)
        return {**state, "findings": [], "error": str(exc)}


def _build_graph() -> Any:
    graph = StateGraph(BloatState)
    graph.add_node("detect", _detect_bloat_node)
    graph.set_entry_point("detect")
    graph.add_edge("detect", END)
    return graph.compile()


_graph = _build_graph()


async def run_bloat_detective(
    layer_data: list[dict],
    manifest: dict,
) -> list[dict]:
    if not layer_data and not manifest:
        logger.info("No layer data available, skipping bloat analysis")
        return []
    result = await _graph.ainvoke(
        {
            "layer_data": layer_data,
            "manifest": manifest,
            "findings": [],
            "error": None,
        }
    )
    return result["findings"]
