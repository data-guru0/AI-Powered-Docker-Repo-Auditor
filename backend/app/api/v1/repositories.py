from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user
from app.models.registry import Repository
from app.services.registry import list_dockerhub_repos, list_ecr_repos
from app.services.dynamodb import get_workspace_repos
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=list[Repository])
async def list_repositories(
    registry_type: str = Query(default="dockerhub"),
    user: dict = Depends(get_current_user),
) -> list[Repository]:
    if registry_type == "dockerhub":
        repos = await list_dockerhub_repos(user["user_id"])
    elif registry_type == "ecr":
        repos = await list_ecr_repos(user["user_id"])
    else:
        return []

    workspace = await get_workspace_repos(user["user_id"])
    workspace_ids = {r["repoId"] for r in workspace}
    for repo in repos:
        repo.inWorkspace = repo.id in workspace_ids
    return repos
