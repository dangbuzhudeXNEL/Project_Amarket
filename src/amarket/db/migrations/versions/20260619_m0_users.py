"""M0 baseline: users table.

Revision ID: 20260619_m0_users
Revises:
Create Date: 2026-06-19 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic
revision: str = "20260619_m0_users"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create `users` table (Spec v3 §7.2)."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=64), nullable=False),
        sa.Column(
            "role",
            sqlmodel.AutoString(),
            nullable=False,
            server_default="admin",
        ),
        sa.Column(
            "timezone",
            sqlmodel.AutoString(length=64),
            nullable=False,
            server_default="Asia/Shanghai",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_name", "users", ["name"])


def downgrade() -> None:
    op.drop_index("ix_users_name", table_name="users")
    op.drop_table("users")
