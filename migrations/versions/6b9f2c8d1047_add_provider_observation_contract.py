"""add provider observation contract

Revision ID: 6b9f2c8d1047
Revises: 5a8d1f73bc44
"""

from alembic import op
import sqlalchemy as sa


revision = "6b9f2c8d1047"
down_revision = "5a8d1f73bc44"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "integration_sources",
        sa.Column("adapter_key", sa.String(length=100), server_default="canonical_v1", nullable=False),
    )
    op.add_column("integration_sources", sa.Column("field_mapping", sa.JSON(), nullable=True))
    op.add_column("integration_sources", sa.Column("allowed_record_types", sa.JSON(), nullable=True))
    op.add_column("integration_sources", sa.Column("authorized_agency_ids", sa.JSON(), nullable=True))
    op.add_column(
        "integration_sources",
        sa.Column("match_threshold", sa.Integer(), server_default="60", nullable=False),
    )
    op.add_column("integration_sources", sa.Column("webhook_secret_hash", sa.String(length=255), nullable=True))

    op.add_column(
        "partner_intake_records",
        sa.Column("suggested_bolo_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_partner_intake_suggested_bolo",
        "partner_intake_records",
        "bolo_alerts",
        ["suggested_bolo_id"],
        ["bolo_id"],
    )
    op.add_column("partner_intake_records", sa.Column("canonical_data", sa.JSON(), nullable=True))
    op.add_column(
        "partner_intake_records",
        sa.Column("schema_version", sa.String(length=20), server_default="1.0", nullable=False),
    )

    op.add_column("bolo_alerts", sa.Column("vehicle_year", sa.Integer(), nullable=True))
    op.add_column("bolo_alerts", sa.Column("vehicle_make", sa.String(length=100), nullable=True))
    op.add_column("bolo_alerts", sa.Column("vehicle_model", sa.String(length=100), nullable=True))
    op.add_column("bolo_alerts", sa.Column("vehicle_color", sa.String(length=100), nullable=True))
    op.add_column("bolo_alerts", sa.Column("plate_number", sa.String(length=32), nullable=True))
    op.add_column("bolo_alerts", sa.Column("plate_state", sa.String(length=16), nullable=True))
    op.add_column("bolo_alerts", sa.Column("vehicle_identifiers", sa.Text(), nullable=True))


def downgrade() -> None:
    for column in (
        "vehicle_identifiers",
        "plate_state",
        "plate_number",
        "vehicle_color",
        "vehicle_model",
        "vehicle_make",
        "vehicle_year",
    ):
        op.drop_column("bolo_alerts", column)

    op.drop_column("partner_intake_records", "schema_version")
    op.drop_column("partner_intake_records", "canonical_data")
    op.drop_constraint("fk_partner_intake_suggested_bolo", "partner_intake_records", type_="foreignkey")
    op.drop_column("partner_intake_records", "suggested_bolo_id")

    for column in (
        "webhook_secret_hash",
        "match_threshold",
        "authorized_agency_ids",
        "allowed_record_types",
        "field_mapping",
        "adapter_key",
    ):
        op.drop_column("integration_sources", column)
