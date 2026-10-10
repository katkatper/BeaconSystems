"""add dashboard query indexes

Revision ID: a7d31c9e4b20
Revises: f6c28db137ba
Create Date: 2026-10-10
"""

from alembic import op


revision = "a7d31c9e4b20"
down_revision = "f6c28db137ba"
branch_labels = None
depends_on = None


DASHBOARD_INDEXES = (
    ("ix_alerts_case_created", "alerts", ["case_id", "created_at"]),
    ("ix_sightings_case_created", "sightings", ["case_id", "created_at"]),
    (
        "ix_agency_exchanges_case_created",
        "agency_exchanges",
        ["case_id", "created_at"],
    ),
    (
        "ix_legal_access_agency_status",
        "legal_access_requests",
        ["agency_id", "status"],
    ),
    (
        "ix_case_access_grants_agency_granted",
        "case_access_grants",
        ["agency_id", "granted_at"],
    ),
)


def upgrade() -> None:
    for index_name, table_name, columns in DASHBOARD_INDEXES:
        op.create_index(index_name, table_name, columns, unique=False)


def downgrade() -> None:
    for index_name, table_name, _columns in reversed(DASHBOARD_INDEXES):
        op.drop_index(index_name, table_name=table_name)
