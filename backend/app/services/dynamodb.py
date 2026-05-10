from typing import Optional
from datetime import datetime, timezone
from app.core.aws import get_dynamodb_resource
from app.core.config import settings
from boto3.dynamodb.conditions import Key, Attr
import logging

logger = logging.getLogger(__name__)


def _table(name: str):
    resource = get_dynamodb_resource()
    table_map = {
        "connections": settings.DYNAMODB_CONNECTIONS_TABLE,
        "scan_jobs": settings.DYNAMODB_SCAN_JOBS_TABLE,
        "scan_results": settings.DYNAMODB_SCAN_RESULTS_TABLE,
        "eval_results": settings.DYNAMODB_EVAL_RESULTS_TABLE,
    }
    return resource.Table(table_map[name])


# ── Workspace repos (stored in connections table with repo# prefix) ──────────

async def get_workspace_repos(user_id: str) -> list[dict]:
    table = _table("connections")
    resp = table.query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        FilterExpression=Attr("connection_id").begins_with("repo#"),
    )
    return [
        {k: v for k, v in item.items() if k not in ("user_id", "connection_id")}
        for item in resp.get("Items", [])
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
    resp = table.query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        FilterExpression=Attr("connection_id").is_in(["ecr", "dockerhub"]),
    )
    return [
        {k: v for k, v in item.items() if k not in ("user_id", "connection_id")}
        for item in resp.get("Items", [])
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
    table = _table("scan_jobs")
    resp = table.query(
        IndexName="RepoIdIndex",
        KeyConditionExpression=Key("repo_id").eq(repo_id),
        FilterExpression=Attr("user_id").eq(user_id),
        ScanIndexForward=False,
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0] if items else None


async def get_scan_result(scan_id: str) -> Optional[dict]:
    table = _table("scan_jobs")
    resp = table.get_item(Key={"job_id": scan_id})
    return resp.get("Item")


async def get_scan_history(user_id: str, repo_id: str) -> list[dict]:
    table = _table("scan_jobs")
    resp = table.query(
        IndexName="RepoIdIndex",
        KeyConditionExpression=Key("repo_id").eq(repo_id),
        FilterExpression=Attr("user_id").eq(user_id),
        ScanIndexForward=False,
        Limit=30,
    )
    return resp.get("Items", [])


# ── Eval scores ──────────────────────────────────────────────────────────────

async def get_eval_scores(user_id: str, repo_id: str) -> list[dict]:
    table = _table("eval_results")
    resp = table.query(
        KeyConditionExpression=Key("job_id").eq(repo_id),
        ScanIndexForward=False,
        Limit=50,
    )
    return resp.get("Items", [])
