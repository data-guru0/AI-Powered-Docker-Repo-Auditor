from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
from app.core.auth import get_current_user
from app.core.rate_limiter import chat_rate_limit
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessageModel(BaseModel):
    role: str
    content: str
    timestamp: str
    sources: Optional[list[str]] = None


class ChatRequestModel(BaseModel):
    message: str
    conversationHistory: list[ChatMessageModel] = []
    repoScope: Optional[list[str]] = None


@router.post("", response_model=ChatMessageModel)
async def chat(
    request: ChatRequestModel,
    user: dict = Depends(chat_rate_limit),
) -> ChatMessageModel:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return ChatMessageModel(
        role="assistant",
        content=(
            "The Chat Agent is running in the worker service. "
            "Results will be streamed via WebSocket when the worker processes your query."
        ),
        timestamp=datetime.now(timezone.utc).isoformat(),
        sources=[],
    )
