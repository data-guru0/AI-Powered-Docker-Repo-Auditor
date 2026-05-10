from fastapi import APIRouter, Request
from app.services.dynamodb import save_ws_connection, delete_ws_connection
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ws/connect")
async def ws_connect(request: Request):
    connection_id = request.headers.get("x-connection-id", "")
    job_id = request.query_params.get("jobId", "")
    logger.info("WS connect: conn=%s job=%s headers=%s", connection_id, job_id, dict(request.headers))
    if connection_id and job_id:
        await save_ws_connection(job_id, connection_id)
        logger.info("WebSocket connected: conn=%s job=%s", connection_id, job_id)
    return {}


@router.post("/ws/disconnect")
async def ws_disconnect(request: Request):
    connection_id = request.headers.get("x-connection-id", "")
    if connection_id:
        await delete_ws_connection(connection_id)
        logger.info("WebSocket disconnected: conn=%s", connection_id)
    return {}


@router.post("/ws/message")
async def ws_message(request: Request):
    connection_id = request.headers.get("x-connection-id", "")
    try:
        body = await request.json()
        if body.get("action") == "subscribe":
            job_id = body.get("jobId", "")
            if connection_id and job_id:
                await save_ws_connection(job_id, connection_id)
                logger.info("WebSocket subscribed: conn=%s job=%s", connection_id, job_id)
    except Exception as exc:
        logger.warning("WebSocket message parse error: %s", exc)
    return {}
