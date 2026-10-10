"""add user authentication version

Revision ID: c39f5a8d04e7
Revises: b28e4f7a93c2
Create Date: 2026-09-19
"""

import sqlalchemy as sa
from alembic import op


revision = "c39f5a8d04e7"
down_revision = "b28e4f7a93c2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "auth_version",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.alter_column("users", "auth_version", server_default=None)


def downgrade():
    op.drop_column("users", "auth_version")
