"""add evidence custody fields

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-06-05 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not has_column("evidence", "custody_status"):
        op.add_column("evidence", sa.Column("custody_status", sa.String(length=100), nullable=True))

    if not has_column("evidence", "current_holder"):
        op.add_column("evidence", sa.Column("current_holder", sa.String(length=200), nullable=True))

    if not has_column("evidence", "lab_reference"):
        op.add_column("evidence", sa.Column("lab_reference", sa.String(length=200), nullable=True))

    if not has_column("evidence", "available_at"):
        op.add_column("evidence", sa.Column("available_at", sa.DateTime(), nullable=True))

    if not has_column("evidence_chain", "from_holder"):
        op.add_column("evidence_chain", sa.Column("from_holder", sa.String(length=200), nullable=True))

    if not has_column("evidence_chain", "to_holder"):
        op.add_column("evidence_chain", sa.Column("to_holder", sa.String(length=200), nullable=True))

    if not has_column("evidence_chain", "location"):
        op.add_column("evidence_chain", sa.Column("location", sa.String(length=200), nullable=True))

    if not has_column("evidence_chain", "available_at"):
        op.add_column("evidence_chain", sa.Column("available_at", sa.DateTime(), nullable=True))

    op.execute("UPDATE evidence SET custody_status = COALESCE(custody_status, 'collected')")


def downgrade() -> None:
    for table_name, column_name in [
        ("evidence_chain", "available_at"),
        ("evidence_chain", "location"),
        ("evidence_chain", "to_holder"),
        ("evidence_chain", "from_holder"),
        ("evidence", "available_at"),
        ("evidence", "lab_reference"),
        ("evidence", "current_holder"),
        ("evidence", "custody_status"),
    ]:
        if has_column(table_name, column_name):
            op.drop_column(table_name, column_name)
