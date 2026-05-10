import json
from datetime import datetime, timezone
from typing import Optional, Any
from app.core.aws import get_dynamodb_resource, get_secrets_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def _table(name: str):
    resource = get_dynamodb_resource()
    return resource.Table(f"{settings.DYNAMODB_TABLE_PREFIX}-{name}")


async def store_scan_result(user_id: str, scan_record: dict) -> None:
    table = _table("scans")
    item = {
        "user_id": user_id,
        "scan_id": scan_record["scan_id"],
        "repo_id": scan_record["repo_id"],
        **scan_record,
    }
    table.put_item(Item=_serialize(item))
    logger.info("Stored scan result %s", scan_record["scan_id"])


async def get_previous_scan(user_id: str, repo_id: str) -> Optional[dict]:
    table = _table("scans")
    resp = table.query(
        KeyConditionExpression="user_id = :uid AND repo_id = :rid",
        ExpressionAttributeValues={":uid": user_id, ":rid": repo_id},
        ScanIndexForward=False,
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0] if items else None


async def update_job_status(
    job_id: str, status: str, progress: int, step: str
) -> None:
    table = _table("job_status")
    table.put_item(
        Item={
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "currentStep": step,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
    )


async def store_eval_scores(user_id: str, repo_id: str, scan_id: str, scores: dict) -> None:
    table = _table("eval_scores")
    for agent_name, agent_scores in scores.items():
        table.put_item(
            Item={
                "user_id": user_id,
                "repo_id": repo_id,
                "scan_id": scan_id,
                "agent_name": agent_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **agent_scores,
            }
        )


async def get_user_credentials(user_id: str) -> dict:
    client = get_secrets_client()
    result: dict = {"user_id": user_id}

    for registry_type in ("dockerhub", "ecr"):
        secret_id = f"{settings.DYNAMODB_TABLE_PREFIX}/users/{user_id}/{registry_type}".replace(
            "docker-auditor", "secret"
        )
        try:
            resp = client.get_secret_value(SecretId=secret_id)
            cred = json.loads(resp["SecretString"])
            result.update(cred)
        except Exception:
            pass

    return result


def _serialize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    if isinstance(obj, float):
        from decimal import Decimal
        return Decimal(str(obj))
    return obj
