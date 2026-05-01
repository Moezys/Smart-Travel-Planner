"""Add webhook_url column to users.

Revision ID: 0004_add_webhook_url
Revises: 0003_add_users_and_runs
Create Date: 2026-05-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_add_webhook_url"
down_revision = "0003_add_users_and_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("webhook_url", sa.String(1000), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "webhook_url")
