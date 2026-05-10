import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from app.core.aws import get_dynamodb_resource, get_secrets_client
from app.core.config import settings
from boto3.dynamodb.conditions import Key, Attr
import logging

logger = logging.getLogger(__name__)


def _table(name: str):
    resource = get_dynamodb_resource()
    table_map = {
        "scan_jobs": settings.DYNAMODB_SCAN_JOBS_TABLE,
        "scan_results": settings.DYNAMODB_SCAN_RESULTS_TABLE,
        "eval_results": settings.DYNAMODB_EVAL_RESULTS_TABLE,
    }
    return resource.Table(table_map[name])


async def init_job_record(job_id: str, user_id: str, repo_id: str, started_at: str) -> None:
    table = _table("scan_jobs")
    now = started_at or datetime.now(timezone.utc).isoformat()
    table.put_item(Item={
        "job_id": job_id,
        "user_id": user_id,
        "repo_id": repo_id,
        "status": "running",
        "progress": 0,
        "currentStep": "Starting",
        "startedAt": now,
        "created_at": now,
        "updatedAt": now,
    })


async def update_job_status(job_id: str, status: str, progress: int, step: str) -> None:
    table = _table("scan_jobs")
    table.update_item(
        Key={"job_id": job_id},
        UpdateExpression="SET #s = :s, progress = :p, currentStep = :c, updatedAt = :u",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": status,
            ":p": progress,
            ":c": step,
            ":u": datetime.now(timezone.utc).isoformat(),
        },
    )


async def store_scan_result(job_id: str, scan_record: dict) -> None:
    table = _table("scan_results")
    item = {"job_id": job_id, **scan_record}
    table.put_item(Item=_serialize(item))
    logger.info("Stored scan result for job %s", job_id)


async def get_previous_scan(user_id: str, repo_id: str) -> Optional[dict]:
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


async def store_eval_scores(job_id: str, repo_id: str, scores: dict) -> None:
    table = _table("eval_results")
    for agent_name, agent_scores in scores.items():
        table.put_item(Item=_serialize({
            "job_id": repo_id,
            "eval_run_id": str(uuid.uuid4()),
            "agent_name": agent_name,
            "scan_id": job_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **agent_scores,
        }))


async def get_user_credentials(user_id: str) -> dict:
    client = get_secrets_client()
    result: dict = {"user_id": user_id}
    for registry_type in ("dockerhub", "ecr"):
        secret_id = f"{settings.SECRET_PREFIX}/users/{user_id}/{registry_type}"
        try:
            resp = client.get_secret_value(SecretId=secret_id)
            result.update(json.loads(resp["SecretString"]))
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
