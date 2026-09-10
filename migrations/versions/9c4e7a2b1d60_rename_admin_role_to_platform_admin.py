"""rename admin role to platform admin

Revision ID: 9c4e7a2b1d60
Revises: 8bb81b58ddda
Create Date: 2026-09-10
"""

from alembic import op


revision = "9c4e7a2b1d60"
down_revision = "8bb81b58ddda"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE users SET role = 'platform_admin' WHERE role = 'admin'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE users SET role = 'admin' WHERE role = 'platform_admin'"
    )
