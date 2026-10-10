"""reconcile the legacy leads table with the managed schema

Revision ID: b8e42da7c531
Revises: a7d31c9e4b20
Create Date: 2026-10-10
"""

import sqlalchemy as sa
from alembic import op


revision = "b8e42da7c531"
down_revision = "a7d31c9e4b20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    table_names = set(sa.inspect(connection).get_table_names())

    if "Leads" in table_names and "leads" in table_names:
        raise RuntimeError(
            'Both legacy "Leads" and managed "leads" tables exist; '
            "merge them before applying this migration."
        )

    if "Leads" in table_names:
        op.rename_table("Leads", "leads")
    elif "leads" not in table_names:
        op.create_table(
            "leads",
            sa.Column("lead_id", sa.Integer(), primary_key=True),
            sa.Column("case_id", sa.Integer(), nullable=True),
            sa.Column("lead_source", sa.String(length=100), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("confidence_score", sa.Float(), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
        )

    existing_indexes = {
        index["name"] for index in sa.inspect(connection).get_indexes("leads")
    }
    if "ix_leads_case_status" not in existing_indexes:
        op.create_index(
            "ix_leads_case_status",
            "leads",
            ["case_id", "status"],
            unique=False,
        )


def downgrade() -> None:
    op.drop_index("ix_leads_case_status", table_name="leads")
    op.rename_table("leads", "Leads")
