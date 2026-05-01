"""User account model.

Password hashing is handled by the auth service (Stage 6).  The column
is named ``hashed_password`` so it is never populated with a plain-text
value by accident.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.run import AgentRun


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Discord / Slack / generic webhook URL — optional, set by the user.
    webhook_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    agent_runs: Mapped[list[AgentRun]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="AgentRun.created_at",
    )
