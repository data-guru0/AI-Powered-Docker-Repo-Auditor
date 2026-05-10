import httpx
import base64
import json
from typing import Optional
from app.models.registry import Repository, RegistryType, ImageTag, LayerInfo
from app.services.secrets import get_credential
import logging

logger = logging.getLogger(__name__)


async def list_dockerhub_repos(user_id: str) -> list[Repository]:
    cred = await get_credential(user_id, "dockerhub")
    if not cred:
        return []

    token = await _get_dockerhub_token(cred["username"], cred["accessToken"])
    repos: list[Repository] = []
    url = f"https://hub.docker.com/v2/repositories/{cred['username']}/?page_size=100"

    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            resp.raise_for_status()
            data = resp.json()
            for r in data.get("results", []):
                repos.append(
                    Repository(
                        id=f"dh-{r['namespace']}-{r['name']}",
                        name=f"{r['namespace']}/{r['name']}",
                        registryType=RegistryType.DOCKERHUB,
                        imageCount=r.get("pull_count", 0),
                        lastPushed=r.get("last_updated", ""),
                        totalSize=r.get("full_size", 0),
                        inWorkspace=False,
                        isPrivate=r.get("is_private", False),
                    )
                )
            url = data.get("next")
    return repos


async def _get_dockerhub_token(username: str, password: str) -> str:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            "https://hub.docker.com/v2/users/login",
            json={"username": username, "password": password},
        )
        resp.raise_for_status()
        return resp.json()["token"]


async def validate_dockerhub_credentials(username: str, access_token: str) -> bool:
    try:
        token = await _get_dockerhub_token(username, access_token)
        return bool(token)
    except Exception:
        return False


async def list_ecr_repos(user_id: str) -> list[Repository]:
    import boto3
    cred = await get_credential(user_id, "ecr")
    if not cred:
        return []

    client = boto3.client(
        "ecr",
        region_name=cred["region"],
        aws_access_key_id=cred["accessKeyId"],
        aws_secret_access_key=cred["secretAccessKey"],
    )

    repos: list[Repository] = []
    paginator = client.get_paginator("describe_repositories")
    for page in paginator.paginate():
        for r in page["repositories"]:
            images = client.describe_images(repositoryName=r["repositoryName"])
            total_size = sum(
                img.get("imageSizeInBytes", 0)
                for img in images.get("imageDetails", [])
            )
            repos.append(
                Repository(
                    id=f"ecr-{r['repositoryName']}",
                    name=r["repositoryName"],
                    registryType=RegistryType.ECR,
                    imageCount=len(images.get("imageDetails", [])),
                    lastPushed=str(r.get("createdAt", "")),
                    totalSize=total_size,
                    inWorkspace=False,
                    isPrivate=True,
                )
            )
    return repos


async def validate_ecr_credentials(access_key_id: str, secret_access_key: str, region: str) -> Optional[str]:
    try:
        import boto3
        client = boto3.client(
            "sts",
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )
        identity = client.get_caller_identity()
        return identity.get("Account")
    except Exception:
        return None
