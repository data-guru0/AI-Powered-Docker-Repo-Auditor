import httpx
import json
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def fetch_manifest(
    repo_id: str,
    image_id: Optional[str],
    user_creds: dict,
) -> dict:
    if "username" in user_creds:
        return await _fetch_dockerhub_manifest(repo_id, image_id, user_creds)
    elif "accessKeyId" in user_creds:
        return await _fetch_ecr_manifest(repo_id, image_id, user_creds)
    return {}


async def _fetch_dockerhub_manifest(
    repo_id: str,
    image_id: Optional[str],
    creds: dict,
) -> dict:
    tag = image_id or "latest"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_resp = await client.post(
                "https://hub.docker.com/v2/users/login",
                json={"username": creds["username"], "password": creds["accessToken"]},
            )
            token_resp.raise_for_status()
            token = token_resp.json()["token"]

            manifest_resp = await client.get(
                f"https://hub.docker.com/v2/repositories/{repo_id}/tags/{tag}",
                headers={"Authorization": f"Bearer {token}"},
            )
            manifest_resp.raise_for_status()
            data = manifest_resp.json()

            return {
                "repoId": repo_id,
                "tag": tag,
                "digest": data.get("digest", ""),
                "size": data.get("full_size", 0),
                "images": data.get("images", []),
                "lastPushed": data.get("tag_last_pushed", ""),
                "baseImage": _extract_base_image(data),
                "dockerfileHistory": [],
            }
    except Exception as exc:
        logger.error("Failed to fetch DockerHub manifest for %s: %s", repo_id, exc)
        return {"repoId": repo_id, "tag": tag}


async def _fetch_ecr_manifest(
    repo_id: str,
    image_id: Optional[str],
    creds: dict,
) -> dict:
    import boto3
    try:
        region = creds.get("region", "us-east-1")
        account_id = creds.get("accountId", "")
        registry_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com" if account_id else ""
        client = boto3.client(
            "ecr",
            region_name=region,
            aws_access_key_id=creds["accessKeyId"],
            aws_secret_access_key=creds["secretAccessKey"],
        )
        tag = image_id or "latest"
        resp = client.batch_get_image(
            repositoryName=repo_id,
            imageIds=[{"imageTag": tag}],
        )
        if resp.get("images"):
            manifest = json.loads(resp["images"][0]["imageManifest"])
            full_uri = f"{registry_uri}/{repo_id}:{tag}" if registry_uri else f"{repo_id}:{tag}"
            return {
                "repoId": repo_id,
                "tag": tag,
                "imageUri": full_uri,
                "manifest": manifest,
            }
        return {"repoId": repo_id, "tag": tag}
    except Exception as exc:
        logger.error("Failed to fetch ECR manifest for %s: %s", repo_id, exc)
        return {"repoId": repo_id}


def _extract_base_image(data: dict) -> str:
    images = data.get("images", [])
    if images:
        return images[0].get("os", "linux")
    return ""
