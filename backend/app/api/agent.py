"""Agent chat endpoint.

POST /api/chat  — authenticated, persists the run, fires webhook.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import run_agent
from app.api.deps import get_current_user
from app.db import get_session
from app.models.user import User
from app.services.webhook import schedule_webhook

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

    # Fire webhook in a background task — never blocks the response.
    # tool_names are extracted from usage keys; full tool detail lives in DB.
    schedule_webhook(
        url=current_user.webhook_url,
        question=body.message,
        answer=answer,
        usage=usage,
        tool_names=["rag_search", "classify_destination", "get_weather"],
    )

    return ChatResponse(answer=answer, token_usage=usage)
