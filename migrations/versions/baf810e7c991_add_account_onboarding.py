"""Add account invitations and access requests."""

import sqlalchemy as sa
from alembic import op

revision = "baf810e7c991"
down_revision = "d91f0bc472aa"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "account_invitations",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("agency_id", sa.Integer(), sa.ForeignKey("agencies.agency_id"), nullable=False),
        sa.Column("issuer_id", sa.Integer(), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime()),
    )
    op.create_table(
        "account_access_requests",
        sa.Column("request_id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("agency_name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("decision", sa.String(16)),
    )


def downgrade():
    op.drop_table("account_access_requests")
    op.drop_table("account_invitations")
