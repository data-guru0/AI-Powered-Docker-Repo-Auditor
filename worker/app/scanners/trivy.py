import json
import os
import subprocess
import base64
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

TRIVY_BIN = next(
    (p for p in ("/usr/bin/trivy", "/usr/local/bin/trivy") if __import__("os").path.exists(p)),
    "/usr/bin/trivy",
)


def _build_image_target(repo_id: str, image_id: Optional[str], user_creds: dict) -> str:
    tag = image_id or "latest"
    if "accessKeyId" in user_creds and "accountId" in user_creds:
        region = user_creds.get("region", "us-east-1")
        account = user_creds["accountId"]
        return f"{account}.dkr.ecr.{region}.amazonaws.com/{repo_id}:{tag}"
    return f"{repo_id}:{tag}"


def _ecr_docker_creds(user_creds: dict) -> tuple[str, str]:
    import boto3
    client = boto3.client(
        "ecr",
        region_name=user_creds.get("region", "us-east-1"),
        aws_access_key_id=user_creds["accessKeyId"],
        aws_secret_access_key=user_creds["secretAccessKey"],
    )
    token = client.get_authorization_token()
    auth = token["authorizationData"][0]["authorizationToken"]
    decoded = base64.b64decode(auth).decode()
    username, password = decoded.split(":", 1)
    return username, password


async def run_trivy_scan(
    repo_id: str,
    image_id: Optional[str],
    user_creds: dict,
) -> dict:
    target = _build_image_target(repo_id, image_id, user_creds)
    logger.info("Trivy scan target: %s (binary: %s)", target, TRIVY_BIN)

    if os.path.exists(TRIVY_BIN):
        return await _run_trivy_local(target, user_creds)
    else:
        logger.info("Trivy binary not found at %s, falling back to Lambda", TRIVY_BIN)
        return await _run_trivy_lambda(target, user_creds)


async def _run_trivy_local(target: str, user_creds: dict) -> dict:
    env = os.environ.copy()
    env.setdefault("TRIVY_CACHE_DIR", "/trivy-cache")

    if "accessKeyId" in user_creds:
        env["AWS_ACCESS_KEY_ID"] = user_creds["accessKeyId"]
        env["AWS_SECRET_ACCESS_KEY"] = user_creds["secretAccessKey"]
        env["AWS_DEFAULT_REGION"] = user_creds.get("region", "us-east-1")
        try:
            username, password = _ecr_docker_creds(user_creds)
            env["TRIVY_USERNAME"] = username
            env["TRIVY_PASSWORD"] = password
        except Exception as exc:
            logger.warning("Could not get ECR docker creds: %s", exc)
    elif "username" in user_creds:
        env["TRIVY_USERNAME"] = user_creds["username"]
        env["TRIVY_PASSWORD"] = user_creds.get("accessToken", "")

    cmd = [
        TRIVY_BIN, "image",
        "--format", "json",
        "--quiet",
        "--no-progress",
        "--scanners", "vuln,secret",
        "--timeout", "10m",
        target,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600, env=env
        )
        if result.returncode != 0:
            logger.error("Trivy exited %d: %s", result.returncode, result.stderr[:500])
            return {"Results": []}
        return json.loads(result.stdout) if result.stdout.strip() else {"Results": []}
    except subprocess.TimeoutExpired:
        logger.error("Trivy scan timed out for %s", target)
        return {"Results": []}
    except Exception as exc:
        logger.error("Trivy local scan failed for %s: %s", target, exc)
        return {"Results": []}


async def _run_trivy_lambda(target: str, user_creds: dict) -> dict:
    from app.core.aws import get_lambda_client
    payload: dict = {
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
        payload["awsAccessKeyId"] = user_creds["accessKeyId"]
        payload["awsSecretAccessKey"] = user_creds["secretAccessKey"]

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
        logger.error("Trivy Lambda scan failed for %s: %s", target, exc)
        return {"Results": []}
