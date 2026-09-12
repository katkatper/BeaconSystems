"""require operational tenant ownership

Revision ID: a17d9c6e42f1
Revises: 9c4e7a2b1d60
Create Date: 2026-09-12
"""

from alembic import op
import sqlalchemy as sa


revision = "a17d9c6e42f1"
down_revision = "9c4e7a2b1d60"
branch_labels = None
depends_on = None


OWNERSHIP_COLUMNS = (
    ("alerts", "recipient_agency_id"),
    ("bolo_alerts", "agency_id"),
    ("case_access_grants", "agency_id"),
    ("case_team_members", "agency_id"),
    ("external_records", "agency_id"),
    ("legal_access_requests", "agency_id"),
    ("matches", "agency_id"),
    ("partner_intake_records", "agency_id"),
)


def upgrade() -> None:
    # Recover ownership only where an authoritative relationship exists.
    op.execute(
        """
        UPDATE bolo_alerts AS item
        SET agency_id = cases.agency_id
        FROM cases
        WHERE item.agency_id IS NULL AND item.case_id = cases.case_id
        """
    )
    op.execute(
        """
        UPDATE case_access_grants AS item
        SET agency_id = users.agency_id
        FROM users
        WHERE item.agency_id IS NULL AND item.user_id = users.user_id
        """
    )
    op.execute(
        """
        UPDATE case_team_members AS item
        SET agency_id = cases.agency_id
        FROM cases
        WHERE item.agency_id IS NULL AND item.case_id = cases.case_id
        """
    )
    op.execute(
        """
        UPDATE external_records AS item
        SET agency_id = cases.agency_id
        FROM cases
        WHERE item.agency_id IS NULL AND item.case_id = cases.case_id
        """
    )
    op.execute(
        """
        UPDATE legal_access_requests AS item
        SET agency_id = users.agency_id
        FROM users
        WHERE item.agency_id IS NULL
          AND item.requested_by_user_id = users.user_id
        """
    )
    op.execute(
        """
        UPDATE matches AS item
        SET agency_id = external_records.agency_id
        FROM external_records
        WHERE item.agency_id IS NULL
          AND item.external_record_id = external_records.id
        """
    )

    connection = op.get_bind()
    unresolved = []
    for table_name, column_name in OWNERSHIP_COLUMNS:
        count = connection.execute(
            sa.text(
                f"SELECT count(*) FROM {table_name} "
                f"WHERE {column_name} IS NULL"
            )
        ).scalar_one()
        if count:
            unresolved.append(f"{table_name}.{column_name}={count}")

    if unresolved:
        raise RuntimeError(
            "Tenant ownership must be resolved before migration: "
            + ", ".join(unresolved)
        )

    for table_name, column_name in OWNERSHIP_COLUMNS:
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.Integer(),
            nullable=False,
        )


def downgrade() -> None:
    for table_name, column_name in reversed(OWNERSHIP_COLUMNS):
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.Integer(),
            nullable=True,
        )
