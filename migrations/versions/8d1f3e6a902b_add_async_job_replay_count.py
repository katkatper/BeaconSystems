"""add async job replay count

Revision ID: 8d1f3e6a902b
Revises: 7c0a4d9e2158
"""

import sqlalchemy as sa
from alembic import op

revision = "8d1f3e6a902b"
down_revision = "7c0a4d9e2158"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "async_jobs",
        sa.Column(
            "replay_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("async_jobs", "replay_count")
