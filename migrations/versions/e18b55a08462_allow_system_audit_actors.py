"""allow system actors in audit records

Revision ID: e18b55a08462
Revises: d07a44f97351
"""

import sqlalchemy as sa
from alembic import op

revision = "e18b55a08462"
down_revision = "d07a44f97351"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "activity_log",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade():
    op.alter_column(
        "activity_log",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
