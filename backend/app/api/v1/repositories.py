from fastapi import APIRouter, Depends, Query
from app.core.auth import get_current_user
from app.models.registry import Repository
from app.services.registry import list_dockerhub_repos, list_ecr_repos
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=list[Repository])
async def list_repositories(
    registry_type: str = Query(default="dockerhub"),
    user: dict = Depends(get_current_user),
) -> list[Repository]:
    if registry_type == "dockerhub":
        return await list_dockerhub_repos(user["user_id"])
    elif registry_type == "ecr":
        return await list_ecr_repos(user["user_id"])
    return []
