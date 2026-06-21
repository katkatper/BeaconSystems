"""add interagency request fields

Revision ID: fc3d4e5f6071
Revises: fb2c3d4e5f60
Create Date: 2026-06-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "fc3d4e5f6071"
down_revision: Union[str, None] = "fb2c3d4e5f60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {
        column["name"] for column in inspector.get_columns(table_name)
    }


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {
        "requesting_officer": sa.Column("requesting_officer", sa.String(length=200), nullable=True),
        "badge_number": sa.Column("badge_number", sa.String(length=80), nullable=True),
        "subject": sa.Column("subject", sa.String(length=255), nullable=True),
        "request_type": sa.Column("request_type", sa.String(length=120), nullable=True),
        "priority": sa.Column("priority", sa.String(length=50), nullable=True),
        "due_date": sa.Column("due_date", sa.DateTime(), nullable=True),
        "delivery_method": sa.Column("delivery_method", sa.String(length=100), nullable=True),
        "requested_records": sa.Column("requested_records", sa.Text(), nullable=True),
        "attachments": sa.Column("attachments", sa.Text(), nullable=True),
        "assigned_to": sa.Column("assigned_to", sa.String(length=200), nullable=True),
        "requested_by": sa.Column("requested_by", sa.Integer(), nullable=True),
        "audit_log": sa.Column("audit_log", sa.Text(), nullable=True),
        "submitted_at": sa.Column("submitted_at", sa.DateTime(), nullable=True),
        "fulfilled_at": sa.Column("fulfilled_at", sa.DateTime(), nullable=True),
    }

    for column_name, column in columns.items():
        if not has_column(inspector, "agency_exchanges", column_name):
            op.add_column("agency_exchanges", column)

    op.execute("UPDATE agency_exchanges SET priority = COALESCE(priority, 'routine')")
    op.execute("UPDATE agency_exchanges SET request_type = COALESCE(request_type, information_type)")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for column_name in [
        "fulfilled_at",
        "submitted_at",
        "audit_log",
        "requested_by",
        "assigned_to",
        "attachments",
        "requested_records",
        "delivery_method",
        "due_date",
        "priority",
        "request_type",
        "subject",
        "badge_number",
        "requesting_officer",
    ]:
        if has_column(inspector, "agency_exchanges", column_name):
            op.drop_column("agency_exchanges", column_name)
