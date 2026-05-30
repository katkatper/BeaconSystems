"""add partner intake match fields

Revision ID: c6d7e8f90123
Revises: f2a9c3d4e5b6
Create Date: 2026-05-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c6d7e8f90123"
down_revision: Union[str, Sequence[str], None] = "f2a9c3d4e5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {
        column["name"]
        for column in inspector.get_columns("partner_intake_records")
    }

    if "suggested_case_id" not in columns:
        op.add_column(
            "partner_intake_records",
            sa.Column("suggested_case_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_partner_intake_suggested_case",
            "partner_intake_records",
            "cases",
            ["suggested_case_id"],
            ["case_id"],
        )

    if "suggested_person_id" not in columns:
        op.add_column(
            "partner_intake_records",
            sa.Column("suggested_person_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_partner_intake_suggested_person",
            "partner_intake_records",
            "persons",
            ["suggested_person_id"],
            ["person_id"],
        )

    if "match_score" not in columns:
        op.add_column(
            "partner_intake_records",
            sa.Column("match_score", sa.Integer(), nullable=True),
        )

    if "match_reason" not in columns:
        op.add_column(
            "partner_intake_records",
            sa.Column("match_reason", sa.Text(), nullable=True),
        )

    if "match_case_status" not in columns:
        op.add_column(
            "partner_intake_records",
            sa.Column("match_case_status", sa.String(length=50), nullable=True),
        )

    if "intake_channel" not in columns:
        op.add_column(
            "partner_intake_records",
            sa.Column(
                "intake_channel",
                sa.String(length=50),
                server_default="manual",
                nullable=False,
            ),
        )
        op.alter_column("partner_intake_records", "intake_channel", server_default=None)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {
        column["name"]
        for column in inspector.get_columns("partner_intake_records")
    }

    if "intake_channel" in columns:
        op.drop_column("partner_intake_records", "intake_channel")

    if "match_case_status" in columns:
        op.drop_column("partner_intake_records", "match_case_status")

    if "match_reason" in columns:
        op.drop_column("partner_intake_records", "match_reason")

    if "match_score" in columns:
        op.drop_column("partner_intake_records", "match_score")

    if "suggested_person_id" in columns:
        op.drop_constraint(
            "fk_partner_intake_suggested_person",
            "partner_intake_records",
            type_="foreignkey",
        )
        op.drop_column("partner_intake_records", "suggested_person_id")

    if "suggested_case_id" in columns:
        op.drop_constraint(
            "fk_partner_intake_suggested_case",
            "partner_intake_records",
            type_="foreignkey",
        )
        op.drop_column("partner_intake_records", "suggested_case_id")
