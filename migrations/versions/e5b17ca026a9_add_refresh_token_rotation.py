"""add refresh token rotation

Revision ID: e5b17ca026a9
Revises: d4a06b9e15f8
Create Date: 2026-09-19
"""
import sqlalchemy as sa
from alembic import op

revision = "e5b17ca026a9"
down_revision = "d4a06b9e15f8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("auth_sessions", sa.Column("refresh_token_hash", sa.String(64), nullable=True))
    op.add_column("auth_sessions", sa.Column("refresh_expires_at", sa.DateTime(), nullable=True))
    op.create_index("ix_auth_sessions_refresh_token_hash", "auth_sessions", ["refresh_token_hash"], unique=True)
    op.create_index("ix_auth_sessions_refresh_expires_at", "auth_sessions", ["refresh_expires_at"])


def downgrade():
    op.drop_index("ix_auth_sessions_refresh_expires_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_refresh_token_hash", table_name="auth_sessions")
    op.drop_column("auth_sessions", "refresh_expires_at")
    op.drop_column("auth_sessions", "refresh_token_hash")
