import json
from app.core.aws import get_s3_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def upload_scan_report(scan_id: str, scan_record: dict) -> str:
    client = get_s3_client()
    key = f"scans/{scan_id}/report.json"

    try:
        client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=json.dumps(scan_record, default=str),
            ContentType="application/json",
        )
        logger.info("Uploaded scan report to s3://%s/%s", settings.S3_BUCKET_NAME, key)
        return f"s3://{settings.S3_BUCKET_NAME}/{key}"
    except Exception as exc:
        logger.error("Failed to upload scan report %s: %s", scan_id, exc)
        return ""


async def upload_eval_log(scan_id: str, eval_data: dict) -> str:
    client = get_s3_client()
    key = f"evals/{scan_id}/ragas.json"

    try:
        client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=json.dumps(eval_data, default=str),
            ContentType="application/json",
        )
        return f"s3://{settings.S3_BUCKET_NAME}/{key}"
    except Exception as exc:
        logger.error("Failed to upload eval log %s: %s", scan_id, exc)
        return ""
