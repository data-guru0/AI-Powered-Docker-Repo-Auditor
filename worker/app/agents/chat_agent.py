import json
from typing import Any, Optional, TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.core.guardrails import validate_chat_input
import operator
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Docker Image Audit Chat Agent with ReAct reasoning.

You help developers and platform engineers understand their container image scan results.
You have access to tools to query scan history, CVEs, findings, and metrics.

Always apply OpenAI moderation principles — refuse harmful or off-topic requests.
Be specific, technical, and actionable in your responses.
When referencing CVEs, always include the CVE ID, severity, and recommended fix."""


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    user_id: str
    repo_scope: list[str]
    scan_context: dict
    response: str


@tool
def query_scan_findings(repo_id: str, severity: Optional[str] = None) -> str:
    """Query scan findings for a repository, optionally filtered by severity."""
    return json.dumps({"repo_id": repo_id, "severity": severity, "findings": []})


@tool
def query_scan_history(repo_id: str) -> str:
    """Query scan history and score trends for a repository."""
    return json.dumps({"repo_id": repo_id, "history": []})


@tool
def query_cve_details(cve_id: str) -> str:
    """Get detailed information about a specific CVE."""
    return json.dumps({"cve_id": cve_id, "details": f"Details for {cve_id}"})


@tool
def estimate_image_size_change(repo_id: str, target_base: str) -> str:
    """Estimate image size change if switching to a different base image."""
    return json.dumps({"repo_id": repo_id, "target_base": target_base, "estimated_delta_mb": 0})


TOOLS = [query_scan_findings, query_scan_history, query_cve_details, estimate_image_size_change]
tool_node = ToolNode(TOOLS)


async def _agent_node(state: ChatState) -> ChatState:
    llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(TOOLS)

    system = SystemMessage(content=SYSTEM_PROMPT)
    messages = [system] + state["messages"]

    try:
        response = await llm.ainvoke(messages)
        return {**state, "messages": [response]}
    except Exception as exc:
        logger.error("Chat agent error: %s", exc)
        error_msg = AIMessage(content=f"I encountered an error processing your request: {exc}")
        return {**state, "messages": [error_msg], "response": error_msg.content}


def _should_continue(state: ChatState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def _extract_response(state: ChatState) -> ChatState:
    last = state["messages"][-1]
    return {**state, "response": last.content if hasattr(last, "content") else ""}


def _build_graph() -> Any:
    graph = StateGraph(ChatState)
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("extract", _extract_response)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: "extract"})
    graph.add_edge("tools", "agent")
    graph.add_edge("extract", END)
    return graph.compile()


_graph = _build_graph()


async def run_chat_agent(
    message: str,
    conversation_history: list[dict],
    user_id: str,
    repo_scope: list[str],
    scan_context: dict,
) -> str:
    rejection = await validate_chat_input(message)
    if rejection:
        logger.info("Chat input blocked by guardrail: %s", rejection)
        return rejection

    messages: list[BaseMessage] = []
    for msg in conversation_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=message))

    result = await _graph.ainvoke(
        {
            "messages": messages,
            "user_id": user_id,
            "repo_scope": repo_scope,
            "scan_context": scan_context,
            "response": "",
        }
    )
    return result.get("response", "")
