"""add tenant keys to intelligence records

Revision ID: fd4e5f607182
Revises: fc3d4e5f6071
Create Date: 2026-08-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fd4e5f607182"
down_revision: Union[str, Sequence[str], None] = "fc3d4e5f6071"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TENANT_TABLES = ("partner_intake_records", "external_records", "matches")


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    for table_name in TENANT_TABLES:
        if table_name not in tables:
            continue

        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "agency_id" not in columns:
            op.add_column(
                table_name,
                sa.Column("agency_id", sa.Integer(), nullable=True),
            )
            op.create_foreign_key(
                f"fk_{table_name}_agency_id_agencies",
                table_name,
                "agencies",
                ["agency_id"],
                ["agency_id"],
            )
            op.create_index(
                f"ix_{table_name}_agency_id",
                table_name,
                ["agency_id"],
                unique=False,
            )

    if "partner_intake_records" in tables:
        op.execute(
            """
            UPDATE partner_intake_records AS intake
            SET agency_id = cases.agency_id
            FROM cases
            WHERE intake.suggested_case_id = cases.case_id
              AND intake.agency_id IS NULL
            """
        )
        op.execute(
            """
            UPDATE partner_intake_records AS intake
            SET agency_id = users.agency_id
            FROM users
            WHERE intake.received_by_user_id = users.user_id
              AND intake.agency_id IS NULL
            """
        )

    if "external_records" in tables:
        op.execute(
            """
            UPDATE external_records AS record
            SET agency_id = cases.agency_id
            FROM cases
            WHERE record.case_id = cases.case_id
              AND record.agency_id IS NULL
            """
        )

    if "matches" in tables:
        op.execute(
            """
            UPDATE matches AS match_record
            SET agency_id = external_records.agency_id
            FROM external_records
            WHERE match_record.external_record_id = external_records.id
              AND match_record.agency_id IS NULL
            """
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    for table_name in reversed(TENANT_TABLES):
        if table_name not in tables:
            continue

        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "agency_id" not in columns:
            continue

        op.drop_index(f"ix_{table_name}_agency_id", table_name=table_name)
        op.drop_constraint(
            f"fk_{table_name}_agency_id_agencies",
            table_name,
            type_="foreignkey",
        )
        op.drop_column(table_name, "agency_id")
