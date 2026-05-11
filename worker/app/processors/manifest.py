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
        ecr = boto3.client(
            "ecr",
            region_name=region,
            aws_access_key_id=creds["accessKeyId"],
            aws_secret_access_key=creds["secretAccessKey"],
        )
        tag = image_id or "latest"
        resp = ecr.batch_get_image(
            repositoryName=repo_id,
            imageIds=[{"imageTag": tag}],
        )
        if not resp.get("images"):
            return {"repoId": repo_id, "tag": tag}

        raw_manifest = json.loads(resp["images"][0]["imageManifest"])
        full_uri = f"{registry_uri}/{repo_id}:{tag}" if registry_uri else f"{repo_id}:{tag}"

        result = {
            "repoId": repo_id,
            "tag": tag,
            "imageUri": full_uri,
            "manifest": raw_manifest,
        }

        # Fetch the image config blob to get ENV, EXPOSE, USER, and Dockerfile history
        config_digest = None
        schema_version = raw_manifest.get("schemaVersion", 2)
        if schema_version == 2:
            config_digest = raw_manifest.get("config", {}).get("digest")
        elif schema_version == 1:
            # v1 manifest has config in history
            pass

        if config_digest:
            try:
                layer_resp = ecr.get_download_url_for_layer(
                    repositoryName=repo_id,
                    layerDigest=config_digest,
                )
                async with httpx.AsyncClient(timeout=30.0) as client:
                    config_resp = await client.get(layer_resp["downloadUrl"])
                    config_resp.raise_for_status()
                    config = config_resp.json()

                container_config = config.get("config", {})
                result["env"] = container_config.get("Env", [])
                result["exposedPorts"] = list(container_config.get("ExposedPorts", {}).keys())
                result["user"] = container_config.get("User", "")
                result["cmd"] = container_config.get("Cmd", [])
                result["entrypoint"] = container_config.get("Entrypoint", [])
                result["dockerfileHistory"] = [
                    h.get("created_by", "") for h in config.get("history", [])
                ]
            except Exception as exc:
                logger.warning("Could not fetch ECR image config for %s: %s", repo_id, exc)

        return result
    except Exception as exc:
        logger.error("Failed to fetch ECR manifest for %s: %s", repo_id, exc)
        return {"repoId": repo_id}


def _extract_base_image(data: dict) -> str:
    images = data.get("images", [])
    if images:
        return images[0].get("os", "linux")
    return ""
