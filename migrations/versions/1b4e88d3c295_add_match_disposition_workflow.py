"""add match disposition workflow

Revision ID: 1b4e88d3c295
Revises: 0a3d77c2b184
"""

import sqlalchemy as sa
from alembic import op

revision = "1b4e88d3c295"
down_revision = "0a3d77c2b184"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE matches SET status = 'pending_review' WHERE status IS NULL")
    op.alter_column("matches", "status", nullable=False)
    op.add_column("matches", sa.Column("disposition_reason", sa.Text(), nullable=True))
    op.add_column("matches", sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True))
    op.add_column("matches", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "matches",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_foreign_key("fk_matches_reviewed_user", "matches", "users", ["reviewed_by_user_id"], ["user_id"])
    op.create_index("ix_matches_agency_status_created", "matches", ["agency_id", "status", "created_at"])


def downgrade():
    op.drop_index("ix_matches_agency_status_created", table_name="matches")
    op.drop_constraint("fk_matches_reviewed_user", "matches", type_="foreignkey")
    op.alter_column("matches", "status", nullable=True)
    for column in ("updated_at", "reviewed_at", "reviewed_by_user_id", "disposition_reason"):
        op.drop_column("matches", column)
