from typing import Optional, Any
from decimal import Decimal
from datetime import datetime, timezone
from app.core.aws import get_dynamodb_resource
from app.core.config import settings
from boto3.dynamodb.conditions import Key, Attr
import logging

logger = logging.getLogger(__name__)


def _deserialize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _deserialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_deserialize(v) for v in obj]
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def _table(name: str):
    resource = get_dynamodb_resource()
    table_map = {
        "connections": settings.DYNAMODB_CONNECTIONS_TABLE,
        "ws_connections": settings.DYNAMODB_WS_CONNECTIONS_TABLE,
        "scan_jobs": settings.DYNAMODB_SCAN_JOBS_TABLE,
        "scan_results": settings.DYNAMODB_SCAN_RESULTS_TABLE,
        "eval_results": settings.DYNAMODB_EVAL_RESULTS_TABLE,
    }
    return resource.Table(table_map[name])


# ── WebSocket connections ────────────────────────────────────────────────────

async def save_ws_connection(job_id: str, connection_id: str) -> None:
    table = _table("ws_connections")
    table.put_item(Item={"job_id": job_id, "connection_id": connection_id})


async def delete_ws_connection(connection_id: str) -> None:
    table = _table("ws_connections")
    resp = table.scan(FilterExpression=Attr("connection_id").eq(connection_id))
    for item in resp.get("Items", []):
        table.delete_item(Key={"job_id": item["job_id"], "connection_id": connection_id})


async def get_ws_connection_ids(job_id: str) -> list[str]:
    table = _table("ws_connections")
    resp = table.query(KeyConditionExpression=Key("job_id").eq(job_id))
    return [item["connection_id"] for item in resp.get("Items", [])]


# ── Workspace repos (stored in connections table with repo# prefix) ──────────

async def get_workspace_repos(user_id: str) -> list[dict]:
    table = _table("connections")
    resp = table.query(KeyConditionExpression=Key("user_id").eq(user_id))
    return [
        {k: v for k, v in item.items() if k not in ("user_id", "connection_id")}
        for item in resp.get("Items", [])
        if item.get("connection_id", "").startswith("repo#")
    ]


async def add_workspace_repo(user_id: str, repo_data: dict) -> dict:
    table = _table("connections")
    item = {
        "user_id": user_id,
        "connection_id": f"repo#{repo_data['repoId']}",
        "addedAt": datetime.now(timezone.utc).isoformat(),
        **repo_data,
    }
    table.put_item(Item=item)
    return item


async def remove_workspace_repo(user_id: str, repo_id: str) -> None:
    table = _table("connections")
    table.delete_item(Key={"user_id": user_id, "connection_id": f"repo#{repo_id}"})


# ── Registry connections ─────────────────────────────────────────────────────

async def get_connection_status(user_id: str) -> list[dict]:
    table = _table("connections")
    resp = table.query(KeyConditionExpression=Key("user_id").eq(user_id))
    return [
        {k: v for k, v in item.items() if k not in ("user_id", "connection_id")}
        for item in resp.get("Items", [])
        if item.get("connection_id") in ("ecr", "dockerhub")
    ]


async def save_connection_status(user_id: str, connections: list[dict]) -> None:
    table = _table("connections")
    for conn_type in ["ecr", "dockerhub"]:
        try:
            table.delete_item(Key={"user_id": user_id, "connection_id": conn_type})
        except Exception:
            pass
    for conn in connections:
        table.put_item(Item={
            "user_id": user_id,
            "connection_id": conn.get("type", "unknown"),
            **conn,
        })


# ── Scans ────────────────────────────────────────────────────────────────────

async def get_latest_scan(user_id: str, repo_id: str) -> Optional[dict]:
    jobs_table = _table("scan_jobs")
    resp = jobs_table.query(
        IndexName="RepoIdIndex",
        KeyConditionExpression=Key("repo_id").eq(repo_id),
        FilterExpression=Attr("user_id").eq(user_id),
        ScanIndexForward=False,
        Limit=1,
    )
    items = resp.get("Items", [])
    if not items:
        return None
    job_id = items[0]["job_id"]
    result = _table("scan_results").get_item(Key={"job_id": job_id})
    item = result.get("Item")
    return _deserialize(item) if item else None


async def get_scan_result(scan_id: str) -> Optional[dict]:
    resp = _table("scan_results").get_item(Key={"job_id": scan_id})
    item = resp.get("Item")
    return _deserialize(item) if item else None


async def get_scan_history(user_id: str, repo_id: str) -> list[dict]:
    jobs_table = _table("scan_jobs")
    resp = jobs_table.query(
        IndexName="RepoIdIndex",
        KeyConditionExpression=Key("repo_id").eq(repo_id),
        FilterExpression=Attr("user_id").eq(user_id),
        ScanIndexForward=False,
        Limit=30,
    )
    jobs = resp.get("Items", [])
    results_table = _table("scan_results")
    history = []
    for job in jobs:
        r = results_table.get_item(Key={"job_id": job["job_id"]})
        item = r.get("Item")
        if item:
            history.append(_deserialize(item))
    return history


# ── Eval scores ──────────────────────────────────────────────────────────────

async def get_eval_scores(user_id: str, repo_id: str) -> list[dict]:
    table = _table("eval_results")
    resp = table.query(
        KeyConditionExpression=Key("job_id").eq(repo_id),
        ScanIndexForward=False,
        Limit=50,
    )
    return resp.get("Items", [])
