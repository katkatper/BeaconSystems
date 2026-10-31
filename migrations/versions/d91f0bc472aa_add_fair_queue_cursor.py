"""add fair queue cursor

Revision ID: d91f0bc472aa
Revises: c8e42a71d905
"""

import sqlalchemy as sa
from alembic import op

revision = "d91f0bc472aa"
down_revision = "c8e42a71d905"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agencies", sa.Column("queue_last_claimed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("agencies", "queue_last_claimed_at")
