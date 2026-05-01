"""Agent run and tool-call log models.

AgentRun  — one row per user question/answer cycle.
ToolCall  — one row per tool invocation within a run.

user_id is nullable so runs work before auth is wired up (Stage 6).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Token counts per model role (cheap = tool-selection, strong = synthesis).
    tokens_cheap_in: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_cheap_out: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_strong_in: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_strong_out: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped[Optional[User]] = relationship(back_populates="agent_runs")
    tool_calls: Mapped[list[ToolCall]] = relationship(
        back_populates="agent_run",
        cascade="all, delete-orphan",
        order_by="ToolCall.called_at",
    )


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_run_id: Mapped[int] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(String(80), nullable=False)
    # Raw dict the LLM passed to the tool — stored as JSON so it stays queryable.
    input_args: Mapped[dict] = mapped_column(JSON, nullable=False)
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    called_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    agent_run: Mapped[AgentRun] = relationship(back_populates="tool_calls")
