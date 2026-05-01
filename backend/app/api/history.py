"""Run history endpoint.

GET /api/history  — returns the last 20 agent runs for the current user,
each with its tool calls.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db import get_session
from app.models.run import AgentRun
from app.models.user import User

router = APIRouter()


# --------------------------------------------------------------------------- #
# Schemas                                                                      #
# --------------------------------------------------------------------------- #

class ToolCallOut(BaseModel):
    tool_name: str
    input_args: dict
    output: str | None
    called_at: datetime
    model_config = {"from_attributes": True}


class RunOut(BaseModel):
    id: int
    question: str
    answer: str | None
    tokens_cheap_in: int
    tokens_cheap_out: int
    tokens_strong_in: int
    tokens_strong_out: int
    created_at: datetime
    tool_calls: list[ToolCallOut]
    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# Route                                                                        #
# --------------------------------------------------------------------------- #

@router.get("/history", response_model=list[RunOut])
async def get_history(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AgentRun]:
    result = await session.execute(
        select(AgentRun)
        .where(AgentRun.user_id == current_user.id)
        .options(selectinload(AgentRun.tool_calls))
        .order_by(AgentRun.created_at.desc())
        .limit(20)
    )
    return list(result.scalars().all())
