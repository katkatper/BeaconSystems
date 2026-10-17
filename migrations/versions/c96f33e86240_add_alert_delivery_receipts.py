"""add durable alert delivery receipts

Revision ID: c96f33e86240
Revises: b84e22d7513f
"""

from alembic import op
import sqlalchemy as sa


revision = "c96f33e86240"
down_revision = "b84e22d7513f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alert_deliveries",
        sa.Column("delivery_id", sa.Integer(), nullable=False),
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("viewed_at", sa.DateTime(), nullable=True),
        sa.Column("viewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.alert_id"]),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.agency_id"]),
        sa.ForeignKeyConstraint(["viewed_by_user_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["acknowledged_by_user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("delivery_id"),
        sa.UniqueConstraint("alert_id", "agency_id", name="uq_alert_deliveries_alert_agency"),
    )
    op.create_index("ix_alert_deliveries_delivery_id", "alert_deliveries", ["delivery_id"])
    op.create_index(
        "ix_alert_deliveries_agency_status",
        "alert_deliveries",
        ["agency_id", "status", "created_at"],
    )
    op.execute("ALTER TABLE alert_deliveries ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY beacon_tenant_isolation ON alert_deliveries
        FOR ALL
        USING (
            current_setting('beacon.platform_admin', true) = 'true'
            OR agency_id = NULLIF(current_setting('beacon.agency_id', true), '')::integer
        )
        WITH CHECK (
            current_setting('beacon.platform_admin', true) = 'true'
            OR agency_id = NULLIF(current_setting('beacon.agency_id', true), '')::integer
        )
        """
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS beacon_tenant_isolation ON alert_deliveries")
    op.drop_index("ix_alert_deliveries_agency_status", table_name="alert_deliveries")
    op.drop_index("ix_alert_deliveries_delivery_id", table_name="alert_deliveries")
    op.drop_table("alert_deliveries")
