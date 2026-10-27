"""normalize partner agency authorization

Revision ID: 7c0a4d9e2158
Revises: 6b9f2c8d1047
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "7c0a4d9e2158"
down_revision = "6b9f2c8d1047"
branch_labels = None
depends_on = None


def _agency_ids(value) -> list[int]:
    if value is None:
        return []
    if isinstance(value, str):
        value = json.loads(value)
    return sorted({int(item) for item in value})


def upgrade() -> None:
    op.create_table(
        "integration_source_agencies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("integration_source_id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("jurisdiction", sa.String(length=255), nullable=True),
        sa.Column("allowed_record_types", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["agency_id"],
            ["agencies.agency_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["integration_source_id"],
            ["integration_sources.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "integration_source_id",
            "agency_id",
            name="uq_integration_source_agency",
        ),
    )
    op.create_index(
        "ix_integration_source_agencies_source",
        "integration_source_agencies",
        ["integration_source_id"],
    )
    op.create_index(
        "ix_integration_source_agencies_agency",
        "integration_source_agencies",
        ["agency_id"],
    )
    op.create_index(
        "ix_bolo_alerts_agency_status_plate",
        "bolo_alerts",
        ["agency_id", "status", "plate_number", "plate_state"],
    )
    op.create_index(
        "ix_bolo_alerts_agency_status_vehicle",
        "bolo_alerts",
        ["agency_id", "status", "vehicle_make", "vehicle_model", "vehicle_color"],
    )
    # Earlier matching jobs could race and create the same candidate twice.
    # Keep the oldest review record before enforcing the database invariant.
    op.execute(
        sa.text(
            "DELETE FROM matches WHERE id IN ("
            "SELECT id FROM ("
            "SELECT id, ROW_NUMBER() OVER ("
            "PARTITION BY agency_id, person_id, external_record_id ORDER BY id"
            ") AS duplicate_number FROM matches"
            ") duplicate_matches WHERE duplicate_number > 1"
            ")"
        )
    )
    op.create_unique_constraint(
        "uq_matches_agency_person_record",
        "matches",
        ["agency_id", "person_id", "external_record_id"],
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, authorized_agency_ids FROM integration_sources")
    ).mappings()
    for row in rows:
        for agency_id in _agency_ids(row["authorized_agency_ids"]):
            connection.execute(
                sa.text(
                    "INSERT INTO integration_source_agencies "
                    "(integration_source_id, agency_id) VALUES (:source_id, :agency_id)"
                ),
                {"source_id": row["id"], "agency_id": agency_id},
            )

    op.drop_column("integration_sources", "authorized_agency_ids")


def downgrade() -> None:
    op.drop_constraint(
        "uq_matches_agency_person_record",
        "matches",
        type_="unique",
    )
    op.drop_index("ix_bolo_alerts_agency_status_vehicle", table_name="bolo_alerts")
    op.drop_index("ix_bolo_alerts_agency_status_plate", table_name="bolo_alerts")
    op.add_column(
        "integration_sources",
        sa.Column("authorized_agency_ids", sa.JSON(), nullable=True),
    )
    connection = op.get_bind()
    source_rows = connection.execute(
        sa.text("SELECT id FROM integration_sources")
    ).mappings()
    for source in source_rows:
        agency_ids = [
            row["agency_id"]
            for row in connection.execute(
                sa.text(
                    "SELECT agency_id FROM integration_source_agencies "
                    "WHERE integration_source_id = :source_id ORDER BY agency_id"
                ),
                {"source_id": source["id"]},
            ).mappings()
        ]
        update_statement = sa.text(
                "UPDATE integration_sources SET authorized_agency_ids = :agency_ids "
                "WHERE id = :source_id"
            ).bindparams(sa.bindparam("agency_ids", type_=sa.JSON()))
        connection.execute(
            update_statement,
            {"agency_ids": agency_ids, "source_id": source["id"]},
        )

    op.drop_index(
        "ix_integration_source_agencies_agency",
        table_name="integration_source_agencies",
    )
    op.drop_index(
        "ix_integration_source_agencies_source",
        table_name="integration_source_agencies",
    )
    op.drop_table("integration_source_agencies")
