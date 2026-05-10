import json
import boto3
from app.core.config import settings
from app.core.aws import get_dynamodb_resource
import logging

logger = logging.getLogger(__name__)


async def publish_progress(
    job_id: str,
    status: str,
    progress: int,
    step: str,
    message: str = "",
) -> None:
    if not settings.API_GATEWAY_WS_ENDPOINT:
        logger.debug("No WebSocket endpoint configured, skipping publish for job %s", job_id)
        return

    event = {
        "jobId": job_id,
        "step": step,
        "progress": progress,
        "status": status,
        "message": message or step,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }

    connection_ids = await _get_connection_ids(job_id)

    if not connection_ids:
        return

    client = boto3.client(
        "apigatewaymanagementapi",
        endpoint_url=settings.API_GATEWAY_WS_ENDPOINT,
        region_name=settings.AWS_REGION,
    )

    payload = json.dumps(event).encode()
    dead_connections: list[str] = []

    for connection_id in connection_ids:
        try:
            client.post_to_connection(
                ConnectionId=connection_id,
                Data=payload,
            )
        except client.exceptions.GoneException:
            dead_connections.append(connection_id)
        except Exception as exc:
            logger.error(
                "Failed to send WebSocket message to %s: %s", connection_id, exc
            )

    if dead_connections:
        await _remove_stale_connections(job_id, dead_connections)


async def _get_connection_ids(job_id: str) -> list[str]:
    try:
        resource = get_dynamodb_resource()
        table = resource.Table(f"{settings.DYNAMODB_TABLE_PREFIX}-ws_connections")
        resp = table.query(
            KeyConditionExpression="job_id = :jid",
            ExpressionAttributeValues={":jid": job_id},
        )
        return [item["connection_id"] for item in resp.get("Items", [])]
    except Exception as exc:
        logger.error("Failed to get WebSocket connections for job %s: %s", job_id, exc)
        return []


async def _remove_stale_connections(job_id: str, connection_ids: list[str]) -> None:
    try:
        resource = get_dynamodb_resource()
        table = resource.Table(f"{settings.DYNAMODB_TABLE_PREFIX}-ws_connections")
        for connection_id in connection_ids:
            table.delete_item(
                Key={"job_id": job_id, "connection_id": connection_id}
            )
    except Exception as exc:
        logger.error("Failed to remove stale connections: %s", exc)
