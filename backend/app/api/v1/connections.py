from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from app.core.auth import get_current_user
from app.models.registry import (
    DockerHubCredentials,
    ECRCredentials,
    Connection,
    ConnectionStatus,
    RegistryType,
)
from app.services.secrets import store_credential, delete_credential
from app.services.registry import validate_dockerhub_credentials, validate_ecr_credentials
from app.services.dynamodb import get_connection_status, save_connection_status
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status", response_model=list[Connection])
async def get_status(user: dict = Depends(get_current_user)) -> list[Connection]:
    stored = await get_connection_status(user["user_id"])
    return [Connection(**c) for c in stored]


@router.post("/dockerhub", response_model=Connection)
async def connect_dockerhub(
    credentials: DockerHubCredentials,
    user: dict = Depends(get_current_user),
) -> Connection:
    valid = await validate_dockerhub_credentials(
        credentials.username, credentials.accessToken
    )
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid DockerHub credentials")

    await store_credential(
        user["user_id"],
        "dockerhub",
        {"username": credentials.username, "accessToken": credentials.accessToken},
    )

    conn = Connection(
        type=RegistryType.DOCKERHUB,
        status=ConnectionStatus.CONNECTED,
        connectedAt=datetime.now(timezone.utc).isoformat(),
        username=credentials.username,
    )

    stored = await get_connection_status(user["user_id"])
    updated = [c for c in stored if c.get("type") != "dockerhub"]
    updated.append(conn.model_dump())
    await save_connection_status(user["user_id"], updated)

    return conn


@router.post("/ecr", response_model=Connection)
async def connect_ecr(
    credentials: ECRCredentials,
    user: dict = Depends(get_current_user),
) -> Connection:
    account_id = await validate_ecr_credentials(
        credentials.accessKeyId,
        credentials.secretAccessKey,
        credentials.region,
    )
    if not account_id:
        raise HTTPException(status_code=400, detail="Invalid ECR credentials")

    await store_credential(
        user["user_id"],
        "ecr",
        {
            "accessKeyId": credentials.accessKeyId,
            "secretAccessKey": credentials.secretAccessKey,
            "region": credentials.region,
        },
    )

    conn = Connection(
        type=RegistryType.ECR,
        status=ConnectionStatus.CONNECTED,
        connectedAt=datetime.now(timezone.utc).isoformat(),
        region=credentials.region,
        accountId=account_id,
    )

    stored = await get_connection_status(user["user_id"])
    updated = [c for c in stored if c.get("type") != "ecr"]
    updated.append(conn.model_dump())
    await save_connection_status(user["user_id"], updated)

    return conn


@router.delete("/{registry_type}")
async def disconnect(
    registry_type: str,
    user: dict = Depends(get_current_user),
) -> dict:
    if registry_type not in ("dockerhub", "ecr"):
        raise HTTPException(status_code=400, detail="Invalid registry type")

    await delete_credential(user["user_id"], registry_type)

    stored = await get_connection_status(user["user_id"])
    updated = [c for c in stored if c.get("type") != registry_type]
    await save_connection_status(user["user_id"], updated)

    return {"status": "disconnected"}
