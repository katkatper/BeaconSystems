"""add alert source fields

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-06-05 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not has_column("alerts", "alert_source"):
        op.add_column("alerts", sa.Column("alert_source", sa.String(length=100), nullable=True))

    if not has_column("alerts", "source_detail"):
        op.add_column("alerts", sa.Column("source_detail", sa.String(length=255), nullable=True))

    if not has_column("alerts", "confidence_score"):
        op.add_column("alerts", sa.Column("confidence_score", sa.Float(), nullable=True))


def downgrade() -> None:
    if has_column("alerts", "confidence_score"):
        op.drop_column("alerts", "confidence_score")

    if has_column("alerts", "source_detail"):
        op.drop_column("alerts", "source_detail")

    if has_column("alerts", "alert_source"):
        op.drop_column("alerts", "alert_source")
