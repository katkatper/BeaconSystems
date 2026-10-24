"""add agency lifecycle controls

Revision ID: 5a8d1f73bc44
Revises: 4e71c9b260aa
"""

import sqlalchemy as sa
from alembic import op

revision = "5a8d1f73bc44"
down_revision = "4e71c9b260aa"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "agencies",
        sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="active"),
    )
    op.add_column("agencies", sa.Column("status_changed_at", sa.DateTime()))
    op.add_column("agencies", sa.Column("status_reason", sa.Text()))
    op.create_check_constraint(
        "ck_agencies_lifecycle_status",
        "agencies",
        "lifecycle_status IN ('active', 'suspended', 'offboarded')",
    )


def downgrade():
    op.drop_constraint("ck_agencies_lifecycle_status", "agencies", type_="check")
    op.drop_column("agencies", "status_reason")
    op.drop_column("agencies", "status_changed_at")
    op.drop_column("agencies", "lifecycle_status")
