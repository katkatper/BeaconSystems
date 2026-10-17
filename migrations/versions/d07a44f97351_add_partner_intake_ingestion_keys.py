"""add partner intake ingestion keys

Revision ID: d07a44f97351
Revises: c96f33e86240
"""

from alembic import op
import sqlalchemy as sa


revision = "d07a44f97351"
down_revision = "c96f33e86240"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "partner_intake_records",
        sa.Column("ingestion_key", sa.String(length=200), nullable=True),
    )
    op.create_unique_constraint(
        "uq_partner_intake_agency_ingestion_key",
        "partner_intake_records",
        ["agency_id", "ingestion_key"],
    )


def downgrade():
    op.drop_constraint(
        "uq_partner_intake_agency_ingestion_key",
        "partner_intake_records",
        type_="unique",
    )
    op.drop_column("partner_intake_records", "ingestion_key")
