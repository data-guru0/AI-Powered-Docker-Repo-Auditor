import json
from app.core.aws import get_s3_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def upload_scan_report(scan_id: str, scan_record: dict) -> str:
    client = get_s3_client()
    bucket = settings.S3_SCAN_REPORTS_BUCKET
    key = f"scans/{scan_id}/report.json"

    try:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(scan_record, default=str),
            ContentType="application/json",
        )
        logger.info("Uploaded scan report to s3://%s/%s", bucket, key)
        return f"s3://{bucket}/{key}"
    except Exception as exc:
        logger.error("Failed to upload scan report %s: %s", scan_id, exc)
        return ""
