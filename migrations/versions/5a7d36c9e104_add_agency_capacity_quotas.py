"""add agency capacity quotas

Revision ID: 5a7d36c9e104
Revises: 8d1f3e6a902b
"""

import sqlalchemy as sa
from alembic import op

revision = "5a7d36c9e104"
down_revision = "8d1f3e6a902b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agencies", sa.Column("storage_quota_bytes", sa.BigInteger(), nullable=True))
    op.add_column(
        "agencies",
        sa.Column("monthly_provider_request_quota", sa.Integer(), nullable=True),
    )
    op.add_column("agencies", sa.Column("monthly_job_quota", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_agencies_storage_quota_positive",
        "agencies",
        "storage_quota_bytes IS NULL OR storage_quota_bytes > 0",
    )
    op.create_check_constraint(
        "ck_agencies_provider_quota_positive",
        "agencies",
        "monthly_provider_request_quota IS NULL OR monthly_provider_request_quota > 0",
    )
    op.create_check_constraint(
        "ck_agencies_job_quota_positive",
        "agencies",
        "monthly_job_quota IS NULL OR monthly_job_quota > 0",
    )
    op.add_column(
        "evidence",
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_partner_intake_agency_received",
        "partner_intake_records",
        ["agency_id", "received_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_partner_intake_agency_received", table_name="partner_intake_records")
    op.drop_column("evidence", "file_size_bytes")
    op.drop_constraint("ck_agencies_job_quota_positive", "agencies", type_="check")
    op.drop_constraint("ck_agencies_provider_quota_positive", "agencies", type_="check")
    op.drop_constraint("ck_agencies_storage_quota_positive", "agencies", type_="check")
    op.drop_column("agencies", "monthly_job_quota")
    op.drop_column("agencies", "monthly_provider_request_quota")
    op.drop_column("agencies", "storage_quota_bytes")
