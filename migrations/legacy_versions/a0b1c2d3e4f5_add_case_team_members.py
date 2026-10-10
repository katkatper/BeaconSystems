"""add case team members

Revision ID: a0b1c2d3e4f5
Revises: f9a0b1c23456
Create Date: 2026-06-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a0b1c2d3e4f5"
down_revision: Union[str, None] = "f9a0b1c23456"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "case_team_members" not in inspector.get_table_names():
        op.create_table(
            "case_team_members",
            sa.Column("team_member_id", sa.Integer(), nullable=False),
            sa.Column("case_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("agency_id", sa.Integer(), nullable=True),
            sa.Column("role", sa.String(length=50), nullable=False, server_default="support_investigator"),
            sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("assigned_by", sa.Integer(), nullable=True),
            sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column("removed_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["agency_id"], ["agencies.agency_id"]),
            sa.ForeignKeyConstraint(["assigned_by"], ["users.user_id"]),
            sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
            sa.PrimaryKeyConstraint("team_member_id"),
        )
        op.create_index(
            "ix_case_team_members_case_id",
            "case_team_members",
            ["case_id"],
        )
        op.create_index(
            "ix_case_team_members_user_id",
            "case_team_members",
            ["user_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "case_team_members" in inspector.get_table_names():
        op.drop_index("ix_case_team_members_user_id", table_name="case_team_members")
        op.drop_index("ix_case_team_members_case_id", table_name="case_team_members")
        op.drop_table("case_team_members")
