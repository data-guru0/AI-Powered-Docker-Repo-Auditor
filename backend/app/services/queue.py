import json
import uuid
from datetime import datetime, timezone
from app.core.aws import get_sqs_client
from app.core.config import settings
from app.models.scan import ScanJob, ScanStatus
import logging

logger = logging.getLogger(__name__)


async def dispatch_scan_job(user_id: str, repo_id: str, image_id: str | None) -> ScanJob:
    job_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    message = {
        "job_id": job_id,
        "user_id": user_id,
        "repo_id": repo_id,
        "image_id": image_id,
        "started_at": started_at,
    }

    client = get_sqs_client()
    client.send_message(
        QueueUrl=settings.SQS_SCAN_QUEUE_URL,
        MessageBody=json.dumps(message),
        MessageGroupId=repo_id,
        MessageDeduplicationId=job_id,
    )

    logger.info("Dispatched scan job %s for repo %s", job_id, repo_id)

    return ScanJob(
        jobId=job_id,
        repoId=repo_id,
        status=ScanStatus.QUEUED,
        progress=0,
        currentStep="Queued",
        startedAt=started_at,
    )
