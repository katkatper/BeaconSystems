"""add compliance workflow tables

Revision ID: 8b71c5f0d4a2
Revises: 1e39221234e2
Create Date: 2026-05-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b71c5f0d4a2"
down_revision: Union[str, Sequence[str], None] = "1e39221234e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evidence",
        sa.Column("is_sensitive", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "evidence",
        sa.Column("file_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "evidence",
        sa.Column("file_path", sa.String(length=500), nullable=True),
    )

    op.create_table(
        "evidence_chain",
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("evidence_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence.evidence_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("chain_id"),
    )
    op.create_index(
        op.f("ix_evidence_chain_chain_id"),
        "evidence_chain",
        ["chain_id"],
        unique=False,
    )

    op.create_table(
        "legal_access_requests",
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("agency_id", sa.Integer(), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("requester_name", sa.String(length=255), nullable=False),
        sa.Column("requester_organization", sa.String(length=255), nullable=False),
        sa.Column("requester_role", sa.String(length=100), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("authority_type", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("target_identifier", sa.String(length=255), nullable=True),
        sa.Column("jurisdiction", sa.String(length=255), nullable=True),
        sa.Column("legal_reference", sa.String(length=255), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("scope_description", sa.Text(), nullable=False),
        sa.Column("minimization_plan", sa.Text(), nullable=True),
        sa.Column("retention_plan", sa.Text(), nullable=True),
        sa.Column("document_location", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.agency_id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index(
        op.f("ix_legal_access_requests_request_id"),
        "legal_access_requests",
        ["request_id"],
        unique=False,
    )

    op.create_table(
        "case_access_grants",
        sa.Column("grant_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("granted_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.agency_id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("grant_id"),
    )
    op.create_index(
        op.f("ix_case_access_grants_grant_id"),
        "case_access_grants",
        ["grant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_case_access_grants_grant_id"),
        table_name="case_access_grants",
    )
    op.drop_table("case_access_grants")

    op.drop_index(
        op.f("ix_legal_access_requests_request_id"),
        table_name="legal_access_requests",
    )
    op.drop_table("legal_access_requests")

    op.drop_index(
        op.f("ix_evidence_chain_chain_id"),
        table_name="evidence_chain",
    )
    op.drop_table("evidence_chain")

    op.drop_column("evidence", "file_path")
    op.drop_column("evidence", "file_name")
    op.drop_column("evidence", "is_sensitive")
