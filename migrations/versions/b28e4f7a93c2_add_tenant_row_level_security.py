"""add tenant row level security

Revision ID: b28e4f7a93c2
Revises: a17d9c6e42f1
Create Date: 2026-09-12
"""

from alembic import op


revision = "b28e4f7a93c2"
down_revision = "a17d9c6e42f1"
branch_labels = None
depends_on = None


TENANT_TABLES = (
    ("cases", "agency_id"),
    ("alerts", "recipient_agency_id"),
    ("bolo_alerts", "agency_id"),
    ("case_access_grants", "agency_id"),
    ("case_team_members", "agency_id"),
    ("external_records", "agency_id"),
    ("legal_access_requests", "agency_id"),
    ("matches", "agency_id"),
    ("partner_intake_records", "agency_id"),
)


def tenant_expression(column_name: str) -> str:
    return f"""
        current_setting('beacon.platform_admin', true) = 'true'
        OR {column_name} = NULLIF(
            current_setting('beacon.agency_id', true), ''
        )::integer
    """


def upgrade() -> None:
    for table_name, column_name in TENANT_TABLES:
        expression = tenant_expression(column_name)
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY beacon_tenant_isolation ON {table_name}
            FOR ALL
            USING ({expression})
            WITH CHECK ({expression})
            """
        )


def downgrade() -> None:
    for table_name, _ in reversed(TENANT_TABLES):
        op.execute(
            f"DROP POLICY beacon_tenant_isolation ON {table_name}"
        )
        op.execute(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY")
