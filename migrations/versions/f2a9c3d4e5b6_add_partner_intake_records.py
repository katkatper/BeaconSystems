"""add partner intake records

Revision ID: f2a9c3d4e5b6
Revises: a4c9d2e8f731
Create Date: 2026-05-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a9c3d4e5b6"
down_revision: Union[str, Sequence[str], None] = "a4c9d2e8f731"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    if "partner_intake_records" in inspector.get_table_names():
        return

    op.create_table(
        "partner_intake_records",
        sa.Column("intake_id", sa.Integer(), nullable=False),
        sa.Column("integration_source_id", sa.Integer(), nullable=False),
        sa.Column("received_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("attached_external_record_id", sa.Integer(), nullable=True),
        sa.Column("record_type", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("subject_name", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["attached_external_record_id"], ["external_records.id"]),
        sa.ForeignKeyConstraint(["integration_source_id"], ["integration_sources.id"]),
        sa.ForeignKeyConstraint(["received_by_user_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("intake_id"),
    )
    op.create_index(
        op.f("ix_partner_intake_records_intake_id"),
        "partner_intake_records",
        ["intake_id"],
        unique=False,
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    if "partner_intake_records" not in inspector.get_table_names():
        return

    op.drop_index(
        op.f("ix_partner_intake_records_intake_id"),
        table_name="partner_intake_records",
    )
    op.drop_table("partner_intake_records")
