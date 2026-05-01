"""Agent chat endpoint.

POST /api/chat  — authenticated, persists the run to the database.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_agent
from app.api.deps import get_current_user
from app.db import get_session
from app.models.user import User

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    token_usage: dict


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    answer, usage = await run_agent(
        body.message,
        session=session,
        user_id=current_user.id,
    )
    return ChatResponse(answer=answer, token_usage=usage)
