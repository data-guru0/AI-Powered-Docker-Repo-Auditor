import asyncio
import json
import signal
import logging
from app.core.aws import get_sqs_client, get_langsmith_api_key, get_openai_api_key
from app.core.config import settings
from app.agents.orchestrator import run_orchestrator
from app.services.dynamodb import update_job_status
from app.services.websocket import publish_progress
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

_shutdown = asyncio.Event()


def _handle_signal(sig, frame):
    logger.info("Received signal %s, shutting down", sig)
    _shutdown.set()


async def process_message(message: dict) -> None:
    body = json.loads(message["Body"])
    job_id = body["job_id"]
    user_id = body["user_id"]
    repo_id = body["repo_id"]
    image_id = body.get("image_id")

    logger.info("Processing scan job %s for repo %s", job_id, repo_id)

    await update_job_status(job_id, "running", 5, "Starting scan")
    await publish_progress(job_id, "running", 5, "Starting scan")

    try:
        await run_orchestrator(job_id, user_id, repo_id, image_id)
    except Exception as exc:
        logger.error("Scan job %s failed: %s", job_id, exc, exc_info=True)
        await update_job_status(job_id, "failed", 0, f"Error: {exc}")
        await publish_progress(job_id, "failed", 0, f"Scan failed: {exc}")


async def poll_sqs() -> None:
    client = get_sqs_client()
    logger.info("Worker started, polling SQS queue: %s", settings.SQS_SCAN_QUEUE_URL)

    while not _shutdown.is_set():
        try:
            resp = client.receive_message(
                QueueUrl=settings.SQS_SCAN_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
                VisibilityTimeout=900,
            )
            messages = resp.get("Messages", [])
            if not messages:
                continue

            for msg in messages:
                try:
                    await process_message(msg)
                    client.delete_message(
                        QueueUrl=settings.SQS_SCAN_QUEUE_URL,
                        ReceiptHandle=msg["ReceiptHandle"],
                    )
                except Exception as exc:
                    logger.error("Failed to process message: %s", exc, exc_info=True)

        except Exception as exc:
            logger.error("SQS polling error: %s", exc)
            await asyncio.sleep(5)


async def main() -> None:
    os.environ["OPENAI_API_KEY"] = get_openai_api_key()
    os.environ["LANGCHAIN_API_KEY"] = get_langsmith_api_key()
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    await poll_sqs()


if __name__ == "__main__":
    asyncio.run(main())
