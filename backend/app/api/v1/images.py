from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.models.registry import ImageTag, LayerInfo
from app.services.secrets import get_credential
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{repo_id}", response_model=list[ImageTag])
async def list_images(
    repo_id: str,
    user: dict = Depends(get_current_user),
) -> list[ImageTag]:
    cred = await get_credential(user["user_id"], "dockerhub") or await get_credential(
        user["user_id"], "ecr"
    )
    if not cred:
        return []

    if "username" in cred:
        return await _list_dockerhub_tags(repo_id, cred)
    return await _list_ecr_images(repo_id, cred)


async def _list_dockerhub_tags(repo_id: str, cred: dict) -> list[ImageTag]:
    import httpx
    from datetime import datetime, timezone

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://hub.docker.com/v2/users/login",
            json={"username": cred["username"], "password": cred["accessToken"]},
        )
        resp.raise_for_status()
        token = resp.json()["token"]

        tags_resp = await client.get(
            f"https://hub.docker.com/v2/repositories/{repo_id}/tags/?page_size=50",
            headers={"Authorization": f"Bearer {token}"},
        )
        tags_resp.raise_for_status()
        data = tags_resp.json()

    images: list[ImageTag] = []
    for tag in data.get("results", []):
        images.append(
            ImageTag(
                id=f"{repo_id}:{tag['name']}",
                repoId=repo_id,
                tag=tag["name"],
                digest=tag.get("digest", ""),
                size=sum(img.get("size", 0) for img in tag.get("images", [])),
                createdAt=tag.get("tag_last_pushed", datetime.now(timezone.utc).isoformat()),
                pushedAt=tag.get("tag_last_pushed", datetime.now(timezone.utc).isoformat()),
                os=tag.get("images", [{}])[0].get("os", "linux") if tag.get("images") else "linux",
                architecture=tag.get("images", [{}])[0].get("architecture", "amd64") if tag.get("images") else "amd64",
            )
        )
    return images


async def _list_ecr_images(repo_id: str, cred: dict) -> list[ImageTag]:
    import boto3

    client = boto3.client(
        "ecr",
        region_name=cred["region"],
        aws_access_key_id=cred["accessKeyId"],
        aws_secret_access_key=cred["secretAccessKey"],
    )
    resp = client.describe_images(repositoryName=repo_id)
    images: list[ImageTag] = []
    for img in resp.get("imageDetails", []):
        for tag in img.get("imageTags", ["<untagged>"]):
            images.append(
                ImageTag(
                    id=f"{repo_id}:{tag}",
                    repoId=repo_id,
                    tag=tag,
                    digest=img.get("imageDigest", ""),
                    size=img.get("imageSizeInBytes", 0),
                    createdAt=str(img.get("imagePushedAt", "")),
                    pushedAt=str(img.get("imagePushedAt", "")),
                )
            )
    return images


@router.get("/{repo_id}/{image_id}/layers", response_model=list[LayerInfo])
async def get_layers(
    repo_id: str,
    image_id: str,
    user: dict = Depends(get_current_user),
) -> list[LayerInfo]:
    return []
