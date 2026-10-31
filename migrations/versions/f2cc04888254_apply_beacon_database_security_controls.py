"""apply Beacon database security controls

Revision ID: f2cc04888254
Revises: 601d95116833
Create Date: 2026-10-10 18:10:43.997081

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f2cc04888254'
down_revision: Union[str, Sequence[str], None] = '601d95116833'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

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
    ("activity_log", "agency_id"),
)


def tenant_expression(column_name: str) -> str:
    return f"""
        current_setting('beacon.platform_admin', true) = 'true'
        OR {column_name} = NULLIF(
            current_setting('beacon.agency_id', true), ''
        )::integer
    """


def upgrade() -> None:
    """Upgrade schema."""
    for table_name, column_name in TENANT_TABLES:
        expression = tenant_expression(column_name)
        op.execute(
            f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"
        )
        op.execute(
            f"""
            CREATE POLICY beacon_tenant_isolation ON {table_name}
            FOR ALL
            USING ({expression})
            WITH CHECK ({expression})
            """
        )

    op.execute(
        """
        CREATE FUNCTION beacon_reject_audit_mutation()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION 'Beacon audit records are append-only'
                USING ERRCODE = '42501';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER beacon_activity_log_append_only
        BEFORE UPDATE OR DELETE ON activity_log
        FOR EACH ROW
        EXECUTE FUNCTION beacon_reject_audit_mutation()
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DROP TRIGGER IF EXISTS "
        "beacon_activity_log_append_only ON activity_log"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS beacon_reject_audit_mutation()"
    )

    for table_name, _ in reversed(TENANT_TABLES):
        op.execute(
            f"DROP POLICY IF EXISTS "
            f"beacon_tenant_isolation ON {table_name}"
        )
        op.execute(
            f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY"
        )
