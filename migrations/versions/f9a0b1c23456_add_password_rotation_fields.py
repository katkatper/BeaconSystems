"""add password rotation fields

Revision ID: f9a0b1c23456
Revises: e8f9a0123456
Create Date: 2026-05-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f9a0b1c23456"
down_revision: Union[str, None] = "e8f9a0123456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_columns = {
        column["name"] for column in inspector.get_columns("users")
    }

    if "password_changed_at" not in existing_columns:
        op.add_column(
            "users",
            sa.Column("password_changed_at", sa.DateTime(), nullable=True),
        )

    if "must_change_password" not in existing_columns:
        op.add_column(
            "users",
            sa.Column("must_change_password", sa.Boolean(), nullable=True),
        )

    op.execute(
        "UPDATE users "
        "SET password_changed_at = COALESCE(password_changed_at, created_at, CURRENT_TIMESTAMP)"
    )
    op.execute(
        "UPDATE users "
        "SET must_change_password = COALESCE(must_change_password, false)"
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {
        column["name"] for column in inspector.get_columns("users")
    }

    if "must_change_password" in existing_columns:
        op.drop_column("users", "must_change_password")

    if "password_changed_at" in existing_columns:
        op.drop_column("users", "password_changed_at")
