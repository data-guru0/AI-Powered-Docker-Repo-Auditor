import json
from typing import Optional, Any
from datetime import datetime, timezone
from app.core.aws import get_dynamodb_resource
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


_TABLE_MAP = {
    "scans": lambda: settings.DYNAMODB_SCAN_JOBS_TABLE,
    "users": lambda: settings.DYNAMODB_CONNECTIONS_TABLE,
    "repos": lambda: settings.DYNAMODB_CONNECTIONS_TABLE,
    "eval_scores": lambda: settings.DYNAMODB_EVAL_RESULTS_TABLE,
}


def _table(name: str):
    resource = get_dynamodb_resource()
    return resource.Table(_TABLE_MAP[name]())


async def get_workspace_repos(user_id: str) -> list[dict]:
    table = _table("repos")
    resp = table.query(
        KeyConditionExpression="user_id = :uid",
        ExpressionAttributeValues={":uid": user_id},
    )
    return resp.get("Items", [])


async def add_workspace_repo(user_id: str, repo_data: dict) -> dict:
    table = _table("repos")
    item = {
        "user_id": user_id,
        "addedAt": datetime.now(timezone.utc).isoformat(),
        **repo_data,
    }
    table.put_item(Item=item)
    return item


async def remove_workspace_repo(user_id: str, repo_id: str) -> None:
    table = _table("repos")
    table.delete_item(Key={"user_id": user_id, "repoId": repo_id})


async def get_latest_scan(user_id: str, repo_id: str) -> Optional[dict]:
    table = _table("scans")
    resp = table.query(
        KeyConditionExpression="user_id = :uid AND repo_id = :rid",
        ExpressionAttributeValues={":uid": user_id, ":rid": repo_id},
        ScanIndexForward=False,
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0] if items else None


async def get_scan_result(scan_id: str) -> Optional[dict]:
    table = _table("scans")
    resp = table.get_item(Key={"scan_id": scan_id})
    return resp.get("Item")


async def get_scan_history(user_id: str, repo_id: str) -> list[dict]:
    table = _table("scans")
    resp = table.query(
        KeyConditionExpression="user_id = :uid AND repo_id = :rid",
        ExpressionAttributeValues={":uid": user_id, ":rid": repo_id},
        ScanIndexForward=False,
        Limit=30,
    )
    return resp.get("Items", [])


async def get_eval_scores(user_id: str, repo_id: str) -> list[dict]:
    table = _table("eval_scores")
    resp = table.query(
        KeyConditionExpression="user_id = :uid AND repo_id = :rid",
        ExpressionAttributeValues={":uid": user_id, ":rid": repo_id},
        ScanIndexForward=False,
        Limit=50,
    )
    return resp.get("Items", [])


async def get_connection_status(user_id: str) -> list[dict]:
    table = _table("users")
    resp = table.get_item(Key={"user_id": user_id})
    item = resp.get("Item", {})
    return item.get("connections", [])


async def save_connection_status(user_id: str, connections: list[dict]) -> None:
    table = _table("users")
    table.update_item(
        Key={"user_id": user_id},
        UpdateExpression="SET connections = :c",
        ExpressionAttributeValues={":c": connections},
    )
