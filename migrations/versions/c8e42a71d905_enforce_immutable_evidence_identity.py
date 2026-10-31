"""enforce immutable evidence identity

Revision ID: c8e42a71d905
Revises: 5a7d36c9e104
"""

import sqlalchemy as sa
from alembic import op

revision = "c8e42a71d905"
down_revision = "5a7d36c9e104"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "integration_sources",
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="120"),
    )
    op.add_column(
        "integration_sources",
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("integration_sources", sa.Column("circuit_open_until", sa.DateTime(), nullable=True))
    op.add_column("integration_sources", sa.Column("last_success_at", sa.DateTime(), nullable=True))
    op.add_column("integration_sources", sa.Column("last_failure_at", sa.DateTime(), nullable=True))
    op.add_column("integration_sources", sa.Column("last_failure_reason", sa.Text(), nullable=True))
    op.add_column("evidence", sa.Column("agency_id", sa.Integer(), nullable=True))
    op.add_column("evidence", sa.Column("preview_path", sa.String(length=500), nullable=True))
    op.add_column("evidence", sa.Column("preview_sha256", sa.String(length=64), nullable=True))
    op.add_column(
        "evidence", sa.Column("preview_size_bytes", sa.BigInteger(), nullable=False, server_default="0")
    )
    op.add_column(
        "evidence", sa.Column("storage_tier", sa.String(length=30), nullable=False, server_default="active")
    )
    op.add_column("evidence", sa.Column("archived_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_evidence_agency_id", "evidence", "agencies", ["agency_id"], ["agency_id"]
    )
    op.execute(
        "UPDATE evidence SET agency_id = cases.agency_id "
        "FROM cases WHERE evidence.case_id = cases.case_id"
    )
    op.alter_column("evidence", "agency_id", nullable=False)
    op.create_index("ix_evidence_agency_id", "evidence", ["agency_id"])
    op.create_index(
        "uq_evidence_agency_content_sha256",
        "evidence",
        ["agency_id", "content_sha256"],
        unique=True,
        postgresql_where=sa.text("content_sha256 IS NOT NULL"),
        sqlite_where=sa.text("content_sha256 IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_evidence_agency_content_sha256", table_name="evidence")
    op.drop_index("ix_evidence_agency_id", table_name="evidence")
    op.drop_constraint("fk_evidence_agency_id", "evidence", type_="foreignkey")
    op.drop_column("evidence", "agency_id")
    op.drop_column("evidence", "archived_at")
    op.drop_column("evidence", "storage_tier")
    op.drop_column("evidence", "preview_size_bytes")
    op.drop_column("evidence", "preview_sha256")
    op.drop_column("evidence", "preview_path")
    op.drop_column("integration_sources", "last_failure_reason")
    op.drop_column("integration_sources", "last_failure_at")
    op.drop_column("integration_sources", "last_success_at")
    op.drop_column("integration_sources", "circuit_open_until")
    op.drop_column("integration_sources", "consecutive_failures")
    op.drop_column("integration_sources", "rate_limit_per_minute")
