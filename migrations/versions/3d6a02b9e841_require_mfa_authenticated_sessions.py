"""require MFA-authenticated sessions

Revision ID: 3d6a02b9e841
Revises: 2c5f91a8d730
"""

import sqlalchemy as sa
from alembic import op

revision = "3d6a02b9e841"
down_revision = "2c5f91a8d730"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "auth_sessions",
        sa.Column(
            "mfa_authenticated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade():
    op.drop_column("auth_sessions", "mfa_authenticated")
