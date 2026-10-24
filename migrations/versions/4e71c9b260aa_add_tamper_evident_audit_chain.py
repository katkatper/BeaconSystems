"""add tamper-evident audit chain

Revision ID: 4e71c9b260aa
Revises: 3d6a02b9e841
"""

import sqlalchemy as sa
from alembic import op

revision = "4e71c9b260aa"
down_revision = "3d6a02b9e841"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("activity_log", sa.Column("previous_hash", sa.String(64)))
    op.add_column("activity_log", sa.Column("event_hash", sa.String(64)))
    op.add_column("activity_log", sa.Column("integrity_key_id", sa.String(100)))
    op.create_index(
        "ix_activity_log_agency_integrity",
        "activity_log",
        ["agency_id", "id", "event_hash"],
    )


def downgrade():
    op.drop_index("ix_activity_log_agency_integrity", table_name="activity_log")
    op.drop_column("activity_log", "integrity_key_id")
    op.drop_column("activity_log", "event_hash")
    op.drop_column("activity_log", "previous_hash")
