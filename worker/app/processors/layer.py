import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def fetch_layer_data(
    repo_id: str,
    image_id: Optional[str],
    user_creds: dict,
) -> list[dict]:
    if "username" in user_creds:
        return await _fetch_dockerhub_layers(repo_id, image_id, user_creds)
    return []


async def _fetch_dockerhub_layers(
    repo_id: str,
    image_id: Optional[str],
    creds: dict,
) -> list[dict]:
    tag = image_id or "latest"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            auth_resp = await client.get(
                f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{repo_id}:pull",
                auth=(creds["username"], creds["accessToken"]),
            )
            auth_resp.raise_for_status()
            token = auth_resp.json()["token"]

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.docker.distribution.manifest.v2+json",
            }
            manifest_resp = await client.get(
                f"https://registry-1.docker.io/v2/{repo_id}/manifests/{tag}",
                headers=headers,
            )
            manifest_resp.raise_for_status()
            manifest = manifest_resp.json()

            layers: list[dict] = []
            for i, layer in enumerate(manifest.get("layers", [])):
                layers.append(
                    {
                        "index": i,
                        "digest": layer.get("digest", ""),
                        "size": layer.get("size", 0),
                        "mediaType": layer.get("mediaType", ""),
                        "command": "",
                        "createdAt": "",
                    }
                )
            return layers
    except Exception as exc:
        logger.error("Failed to fetch layers for %s: %s", repo_id, exc)
        return []
