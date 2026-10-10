"""bridge missing local revision

Revision ID: befeb8da77b5
Revises: 8b71c5f0d4a2
Create Date: 2026-05-25

This no-op migration preserves a revision id that was already stamped in the
local database but was not present in source control. Keeping the id in the
chain lets Alembic apply later migrations normally.
"""

from typing import Sequence, Union


revision: str = "befeb8da77b5"
down_revision: Union[str, Sequence[str], None] = "8b71c5f0d4a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
