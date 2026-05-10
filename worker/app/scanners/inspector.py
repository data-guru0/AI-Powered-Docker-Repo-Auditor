import boto3
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def run_inspector_scan(
    repo_id: str,
    image_id: Optional[str],
    user_creds: dict,
) -> dict:
    if "username" in user_creds:
        return {}

    try:
        region = user_creds.get("region", settings.AWS_REGION)
        client = boto3.client(
            "inspector2",
            region_name=region,
            aws_access_key_id=user_creds.get("accessKeyId"),
            aws_secret_access_key=user_creds.get("secretAccessKey"),
        )

        filters = {
            "ecrImageRepositoryName": [{"comparison": "EQUALS", "value": repo_id}]
        }
        if image_id:
            filters["ecrImageTags"] = [{"comparison": "EQUALS", "value": image_id}]

        findings_response = client.list_findings(filterCriteria=filters)
        return {
            "findings": findings_response.get("findings", []),
            "nextToken": findings_response.get("nextToken"),
        }
    except Exception as exc:
        logger.error("Inspector scan failed for %s: %s", repo_id, exc)
        return {"findings": []}
