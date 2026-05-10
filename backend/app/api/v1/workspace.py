import uuid
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from app.core.auth import get_current_user
from app.models.registry import WorkspaceRepo, RegistryType
from app.services.dynamodb import (
    get_workspace_repos,
    add_workspace_repo,
    remove_workspace_repo,
    get_latest_scan,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/repos", response_model=list[WorkspaceRepo])
async def list_workspace_repos(
    user: dict = Depends(get_current_user),
) -> list[WorkspaceRepo]:
    items = await get_workspace_repos(user["user_id"])
    result: list[WorkspaceRepo] = []
    for item in items:
        scan = await get_latest_scan(user["user_id"], item["repoId"])
        result.append(
            WorkspaceRepo(
                id=item.get("id", str(uuid.uuid4())),
                repoId=item["repoId"],
                name=item["name"],
                registryType=RegistryType(item.get("registryType", "dockerhub")),
                lastScanDate=scan["scanDate"] if scan else None,
                overallGrade=scan["scores"]["overall"] if scan else None,
                criticalCveCount=(
                    scan.get("cveCount", {}).get("critical", 0) if scan else 0
                ),
                addedAt=item["addedAt"],
            )
        )
    return result


@router.post("/repos/{repo_id}", response_model=WorkspaceRepo)
async def add_repo_to_workspace(
    repo_id: str,
    user: dict = Depends(get_current_user),
) -> WorkspaceRepo:
    repo_data = {
        "id": str(uuid.uuid4()),
        "repoId": repo_id,
        "name": repo_id,
        "registryType": "dockerhub",
    }
    item = await add_workspace_repo(user["user_id"], repo_data)
    return WorkspaceRepo(
        id=item["id"],
        repoId=repo_id,
        name=repo_id,
        registryType=RegistryType.DOCKERHUB,
        criticalCveCount=0,
        addedAt=item["addedAt"],
    )


@router.delete("/repos/{repo_id}")
async def remove_repo_from_workspace(
    repo_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    await remove_workspace_repo(user["user_id"], repo_id)
    return {"status": "removed"}
