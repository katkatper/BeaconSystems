"""merge phase zero migration heads

Revision ID: fe5f60718293
Revises: c2d3e4f5a6b7, fd4e5f607182
Create Date: 2026-08-09
"""

from typing import Sequence, Union


revision: str = "fe5f60718293"
down_revision: Union[str, Sequence[str], None] = (
    "c2d3e4f5a6b7",
    "fd4e5f607182",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
