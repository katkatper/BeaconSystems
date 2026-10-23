"""add investigator notifications

Revision ID: 2c5f91a8d730
Revises: 1b4e88d3c295
"""

import sqlalchemy as sa
from alembic import op

revision = "2c5f91a8d730"
down_revision = "1b4e88d3c295"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.agency_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
        sa.PrimaryKeyConstraint("notification_id"),
        sa.UniqueConstraint(
            "user_id", "notification_type", "entity_type", "entity_id",
            name="uq_notifications_user_entity_type",
        ),
    )
    op.create_index("ix_notifications_notification_id", "notifications", ["notification_id"])
    op.create_index(
        "ix_notifications_user_read_created",
        "notifications",
        ["user_id", "read_at", "created_at"],
    )
    op.create_index(
        "ix_notifications_agency_created", "notifications", ["agency_id", "created_at"]
    )
    op.execute("ALTER TABLE notifications ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY beacon_tenant_isolation ON notifications
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
    op.execute("DROP POLICY IF EXISTS beacon_tenant_isolation ON notifications")
    op.drop_index("ix_notifications_agency_created", table_name="notifications")
    op.drop_index("ix_notifications_user_read_created", table_name="notifications")
    op.drop_index("ix_notifications_notification_id", table_name="notifications")
    op.drop_table("notifications")
