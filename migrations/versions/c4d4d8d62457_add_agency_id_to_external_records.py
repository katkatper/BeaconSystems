"""add agency id to external records

Revision ID: c4d4d8d62457
Revises: 0a6f708294b1
"""

from alembic import op
import sqlalchemy as sa


revision = "c4d4d8d62457"
down_revision = "0a6f708294b1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "external_records",
        sa.Column(
            "agency_id",
            sa.Integer(),
            nullable=True
        )
    )

    op.create_index(
        "ix_external_records_agency_id",
        "external_records",
        ["agency_id"],
        unique=False
    )

    op.create_foreign_key(
        "fk_external_records_agency_id_agencies",
        "external_records",
        "agencies",
        ["agency_id"],
        ["agency_id"]
    )


def downgrade():
    op.drop_constraint(
        "fk_external_records_agency_id_agencies",
        "external_records",
        type_="foreignkey"
    )

    op.drop_index(
        "ix_external_records_agency_id",
        table_name="external_records"
    )

    op.drop_column(
        "external_records",
        "agency_id"
    )
.venv/
uploads/