"""enforce agency ownership on users and cases

Revision ID: 8bb81b58ddda
Revises: 5bdef8106da8
Create Date: 2026-09-02 08:27:59.360868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bb81b58ddda'
down_revision: Union[str, Sequence[str], None] = '5bdef8106da8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        "users",
        "agency_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "cases",
        "agency_id",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        "cases",
        "agency_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    op.alter_column(
        "users",
        "agency_id",
        existing_type=sa.Integer(),
        nullable=True,
    )