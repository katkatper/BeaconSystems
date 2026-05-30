"""add partner intake legal authority

Revision ID: d7e8f9012345
Revises: c6d7e8f90123
Create Date: 2026-05-30 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7e8f9012345"
down_revision: Union[str, None] = "c6d7e8f90123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(
        column["name"] == column_name
        for column in inspector.get_columns(table_name)
    )


def upgrade() -> None:
    if not has_column("partner_intake_records", "legal_authority_type"):
        op.add_column(
            "partner_intake_records",
            sa.Column("legal_authority_type", sa.String(length=100), nullable=True),
        )

    if not has_column("partner_intake_records", "legal_authority_reference"):
        op.add_column(
            "partner_intake_records",
            sa.Column("legal_authority_reference", sa.String(length=255), nullable=True),
        )

    if not has_column("partner_intake_records", "legal_authority_notes"):
        op.add_column(
            "partner_intake_records",
            sa.Column("legal_authority_notes", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    if has_column("partner_intake_records", "legal_authority_notes"):
        op.drop_column("partner_intake_records", "legal_authority_notes")

    if has_column("partner_intake_records", "legal_authority_reference"):
        op.drop_column("partner_intake_records", "legal_authority_reference")

    if has_column("partner_intake_records", "legal_authority_type"):
        op.drop_column("partner_intake_records", "legal_authority_type")
