"""add agency exchanges

Revision ID: e8f9a0123456
Revises: d7e8f9012345
Create Date: 2026-05-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e8f9a0123456"
down_revision: Union[str, None] = "d7e8f9012345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("agency_exchanges"):
        op.create_table(
            "agency_exchanges",
            sa.Column("exchange_id", sa.Integer(), nullable=False),
            sa.Column("case_id", sa.Integer(), nullable=False),
            sa.Column("from_agency", sa.String(length=200), nullable=False),
            sa.Column("to_agency", sa.String(length=200), nullable=False),
            sa.Column("information_type", sa.String(length=100), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("legal_authority", sa.String(length=200), nullable=True),
            sa.Column("approved_by", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=50), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["approved_by"], ["users.user_id"]),
            sa.ForeignKeyConstraint(["case_id"], ["cases.case_id"]),
            sa.PrimaryKeyConstraint("exchange_id"),
        )
        inspector = sa.inspect(bind)

    existing_indexes = {
        index["name"] for index in inspector.get_indexes("agency_exchanges")
    }

    indexes = [
        (op.f("ix_agency_exchanges_exchange_id"), ["exchange_id"]),
        ("ix_agency_exchanges_case_id", ["case_id"]),
        ("ix_agency_exchanges_approved_by", ["approved_by"]),
        ("ix_agency_exchanges_created_at", ["created_at"]),
    ]

    for index_name, columns in indexes:
        if index_name not in existing_indexes:
            op.create_index(index_name, "agency_exchanges", columns, unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("agency_exchanges"):
        existing_indexes = {
            index["name"] for index in inspector.get_indexes("agency_exchanges")
        }

        for index_name in [
            "ix_agency_exchanges_created_at",
            "ix_agency_exchanges_approved_by",
            "ix_agency_exchanges_case_id",
            op.f("ix_agency_exchanges_exchange_id"),
        ]:
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name="agency_exchanges")

        op.drop_table("agency_exchanges")
