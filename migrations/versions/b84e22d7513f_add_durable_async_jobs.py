"""add durable tenant-scoped async jobs

Revision ID: b84e22d7513f
Revises: a73d11c6402e
"""

import sqlalchemy as sa
from alembic import op

revision = "b84e22d7513f"
down_revision = "a73d11c6402e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "async_jobs",
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("agency_id", sa.Integer(), nullable=False),
        sa.Column("job_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("available_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
        sa.Column("locked_by", sa.String(length=200), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.agency_id"]),
        sa.PrimaryKeyConstraint("job_id"),
        sa.UniqueConstraint("agency_id", "idempotency_key", name="uq_async_jobs_agency_idempotency"),
    )
    op.create_index("ix_async_jobs_job_id", "async_jobs", ["job_id"])
    op.create_index(
        "ix_async_jobs_claim",
        "async_jobs",
        ["status", "available_at", "priority", "created_at"],
    )
    op.create_index("ix_async_jobs_agency_created", "async_jobs", ["agency_id", "created_at"])
    op.execute("ALTER TABLE async_jobs ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY beacon_tenant_isolation ON async_jobs
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
    op.execute("DROP POLICY IF EXISTS beacon_tenant_isolation ON async_jobs")
    op.drop_index("ix_async_jobs_agency_created", table_name="async_jobs")
    op.drop_index("ix_async_jobs_claim", table_name="async_jobs")
    op.drop_index("ix_async_jobs_job_id", table_name="async_jobs")
    op.drop_table("async_jobs")
