"""add mfa secret to users

Revision ID: fb2c3d4e5f60
Revises: fa1b2c3d4e5f
Create Date: 2026-06-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "fb2c3d4e5f60"
down_revision: Union[str, None] = "fa1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {
        column["name"] for column in inspector.get_columns(table_name)
    }


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not has_column(inspector, "users", "mfa_secret"):
        op.add_column("users", sa.Column("mfa_secret", sa.String(length=255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if has_column(inspector, "users", "mfa_secret"):
        op.drop_column("users", "mfa_secret")
