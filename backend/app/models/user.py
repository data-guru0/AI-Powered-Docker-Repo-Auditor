from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    user_id: str
    email: str


class UserProfile(BaseModel):
    user_id: str
    email: str
    createdAt: str
    workspaceRepoIds: list[str] = []
    policyThresholds: Optional[dict] = None
