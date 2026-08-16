"""add alerts recipient agency foreign key

Revision ID: 30a2e0484047
Revises: c4d4d8d62457
Create Date: 2026-08-16 08:24:12.774581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30a2e0484047'
down_revision: Union[str, Sequence[str], None] = 'c4d4d8d62457'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
