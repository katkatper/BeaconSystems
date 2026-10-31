"""add evidence retention and legal hold controls

Revision ID: a73d11c6402e
Revises: f2cc04888254
"""

import sqlalchemy as sa
from alembic import op

revision = "a73d11c6402e"
down_revision = "f2cc04888254"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "evidence",
        sa.Column(
            "retention_policy_code",
            sa.String(length=100),
            nullable=False,
            server_default="agency-standard",
        ),
    )
    op.add_column("evidence", sa.Column("retention_until", sa.DateTime(), nullable=True))
    op.add_column(
        "evidence",
        sa.Column("legal_hold", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("evidence", sa.Column("legal_hold_reason", sa.Text(), nullable=True))
    op.add_column("evidence", sa.Column("legal_hold_set_at", sa.DateTime(), nullable=True))
    op.add_column("evidence", sa.Column("legal_hold_set_by", sa.Integer(), nullable=True))
    op.add_column(
        "evidence",
        sa.Column(
            "disposition_status",
            sa.String(length=50),
            nullable=False,
            server_default="active",
        ),
    )
    op.create_foreign_key(
        "fk_evidence_legal_hold_set_by_users",
        "evidence",
        "users",
        ["legal_hold_set_by"],
        ["user_id"],
    )
    op.create_check_constraint(
        "ck_evidence_legal_hold_reason",
        "evidence",
        "legal_hold = false OR legal_hold_reason IS NOT NULL",
    )
    op.create_index(
        "ix_evidence_retention_disposition",
        "evidence",
        ["legal_hold", "disposition_status", "retention_until"],
    )


def downgrade():
    op.drop_index("ix_evidence_retention_disposition", table_name="evidence")
    op.drop_constraint("ck_evidence_legal_hold_reason", "evidence", type_="check")
    op.drop_constraint("fk_evidence_legal_hold_set_by_users", "evidence", type_="foreignkey")
    op.drop_column("evidence", "disposition_status")
    op.drop_column("evidence", "legal_hold_set_by")
    op.drop_column("evidence", "legal_hold_set_at")
    op.drop_column("evidence", "legal_hold_reason")
    op.drop_column("evidence", "legal_hold")
    op.drop_column("evidence", "retention_until")
    op.drop_column("evidence", "retention_policy_code")
