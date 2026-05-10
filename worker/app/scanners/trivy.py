import json
from typing import Optional
from app.core.aws import get_lambda_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def run_trivy_scan(
    repo_id: str,
    image_id: Optional[str],
    user_creds: dict,
) -> dict:
    target = f"{repo_id}:{image_id}" if image_id else repo_id

    payload = {
        "target": target,
        "scanners": ["vuln", "secret"],
        "severity": ["UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
        "format": "json",
    }

    if "username" in user_creds:
        payload["registry"] = {
            "username": user_creds["username"],
            "password": user_creds.get("accessToken", ""),
        }
    elif "accessKeyId" in user_creds:
        payload["awsRegion"] = user_creds.get("region", settings.AWS_REGION)

    try:
        client = get_lambda_client()
        resp = client.invoke(
            FunctionName=settings.TRIVY_LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode(),
        )
        result_bytes = resp["Payload"].read()
        result = json.loads(result_bytes)

        if resp.get("FunctionError"):
            logger.error("Trivy Lambda error: %s", result)
            return {"Results": []}

        return result
    except Exception as exc:
        logger.error("Trivy scan failed for %s: %s", target, exc)
        return {"Results": []}
