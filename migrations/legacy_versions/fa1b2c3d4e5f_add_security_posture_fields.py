"""add security posture fields

Revision ID: fa1b2c3d4e5f
Revises: f9a0b1c23456
Create Date: 2026-06-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "fa1b2c3d4e5f"
down_revision: Union[str, None] = "f9a0b1c23456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {
        column["name"] for column in inspector.get_columns(table_name)
    }


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not has_column(inspector, "users", "mfa_enabled"):
        op.add_column(
            "users",
            sa.Column("mfa_enabled", sa.Boolean(), nullable=True),
        )

    if not has_column(inspector, "users", "mfa_verified_at"):
        op.add_column(
            "users",
            sa.Column("mfa_verified_at", sa.DateTime(), nullable=True),
        )

    if not has_column(inspector, "users", "last_login_at"):
        op.add_column(
            "users",
            sa.Column("last_login_at", sa.DateTime(), nullable=True),
        )

    if not has_column(inspector, "evidence", "is_encrypted"):
        op.add_column(
            "evidence",
            sa.Column("is_encrypted", sa.Boolean(), nullable=True),
        )

    if not has_column(inspector, "evidence", "encryption_key_id"):
        op.add_column(
            "evidence",
            sa.Column("encryption_key_id", sa.String(length=120), nullable=True),
        )

    if not has_column(inspector, "evidence", "content_sha256"):
        op.add_column(
            "evidence",
            sa.Column("content_sha256", sa.String(length=64), nullable=True),
        )

    op.execute("UPDATE users SET mfa_enabled = COALESCE(mfa_enabled, false)")
    op.execute("UPDATE evidence SET is_encrypted = COALESCE(is_encrypted, false)")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for column_name in ["content_sha256", "encryption_key_id", "is_encrypted"]:
        if has_column(inspector, "evidence", column_name):
            op.drop_column("evidence", column_name)

    for column_name in ["last_login_at", "mfa_verified_at", "mfa_enabled"]:
        if has_column(inspector, "users", column_name):
            op.drop_column("users", column_name)
