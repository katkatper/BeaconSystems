"""apply alerts recipient agency foreign key

Revision ID: 5bdef8106da8
Revises: 30a2e0484047
"""

from alembic import op


revision = "5bdef8106da8"
down_revision = "30a2e0484047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_foreign_key(
        "fk_alerts_recipient_agency_id_agencies",
        "alerts",
        "agencies",
        ["recipient_agency_id"],
        ["agency_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_alerts_recipient_agency_id_agencies",
        "alerts",
        type_="foreignkey",
    )