"""Persist agent runs and tool-call logs to the database.

Called from run_agent() after the LangGraph graph finishes.  The full
message list is walked once to pair AIMessage.tool_calls entries with
their ToolMessage results by tool_call_id.
"""

from __future__ import annotations

from datetime import datetime, timezone

from langchain_core.messages import BaseMessage, ToolMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import AgentRun, ToolCall


async def log_run(
    session: AsyncSession,
    question: str,
    answer: str,
    token_usage: dict,
    messages: list[BaseMessage],
    user_id: int | None = None,
) -> AgentRun:
    """Persist one agent run and all tool calls that occurred within it."""
    run = AgentRun(
        user_id=user_id,
        question=question,
        answer=answer,
        tokens_cheap_in=token_usage.get("cheap_in", 0),
        tokens_cheap_out=token_usage.get("cheap_out", 0),
        tokens_strong_in=token_usage.get("strong_in", 0),
        tokens_strong_out=token_usage.get("strong_out", 0),
    )
    session.add(run)
    await session.flush()  # populate run.id before inserting ToolCall rows

    # Index ToolMessage results by their tool_call_id for O(1) lookup.
    tool_results: dict[str, str] = {
        msg.tool_call_id: (
            msg.content if isinstance(msg.content, str) else str(msg.content)
        )
        for msg in messages
        if isinstance(msg, ToolMessage)
    }

    called_at = datetime.now(timezone.utc)
    for msg in messages:
        tool_calls = getattr(msg, "tool_calls", None)
        if not tool_calls:
            continue
        for tc in tool_calls:
            session.add(
                ToolCall(
                    agent_run_id=run.id,
                    tool_name=tc["name"],
                    input_args=tc.get("args", {}),
                    output=tool_results.get(tc["id"]),
                    called_at=called_at,
                )
            )

    await session.commit()
    return run
