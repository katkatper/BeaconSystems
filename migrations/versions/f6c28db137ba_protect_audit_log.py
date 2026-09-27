"""protect audit log with tenant RLS and append-only enforcement

Revision ID: f6c28db137ba
Revises: e5b17ca026a9
Create Date: 2026-09-27
"""

from alembic import op


revision = "f6c28db137ba"
down_revision = "e5b17ca026a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY beacon_tenant_isolation ON activity_log
        FOR ALL
        USING (
            current_setting('beacon.platform_admin', true) = 'true'
            OR agency_id = NULLIF(
                current_setting('beacon.agency_id', true), ''
            )::integer
        )
        WITH CHECK (
            current_setting('beacon.platform_admin', true) = 'true'
            OR agency_id = NULLIF(
                current_setting('beacon.agency_id', true), ''
            )::integer
        )
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
        FOR EACH ROW EXECUTE FUNCTION beacon_reject_audit_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER beacon_activity_log_append_only ON activity_log")
    op.execute("DROP FUNCTION beacon_reject_audit_mutation()")
    op.execute("DROP POLICY beacon_tenant_isolation ON activity_log")
    op.execute("ALTER TABLE activity_log DISABLE ROW LEVEL SECURITY")
