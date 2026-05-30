"""add case access review fields

Revision ID: a4c9d2e8f731
Revises: 8b71c5f0d4a2
Create Date: 2026-05-25
"""

from alembic import op
import sqlalchemy as sa


revision = "a4c9d2e8f731"
down_revision = "befeb8da77b5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "case_access_grants",
        sa.Column("reason_category", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "case_access_grants",
        sa.Column("approval_type", sa.String(length=50), nullable=False, server_default="manual"),
    )
    op.add_column(
        "case_access_grants",
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
    )
    op.add_column(
        "case_access_grants",
        sa.Column("review_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "case_access_grants",
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.create_foreign_key(
        "fk_case_access_grants_reviewed_by_users",
        "case_access_grants",
        "users",
        ["reviewed_by"],
        ["user_id"],
    )


def downgrade():
    op.drop_constraint(
        "fk_case_access_grants_reviewed_by_users",
        "case_access_grants",
        type_="foreignkey",
    )
    op.drop_column("case_access_grants", "expires_at")
    op.drop_column("case_access_grants", "review_notes")
    op.drop_column("case_access_grants", "reviewed_by")
    op.drop_column("case_access_grants", "approval_type")
    op.drop_column("case_access_grants", "reason_category")
