"""add lead ownership workflow

Revision ID: 0a3d77c2b184
Revises: f29c66b19573
"""

from alembic import op
import sqlalchemy as sa


revision = "0a3d77c2b184"
down_revision = "f29c66b19573"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("leads", sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"))
    op.add_column("leads", sa.Column("assigned_to_user_id", sa.Integer(), nullable=True))
    op.add_column("leads", sa.Column("due_at", sa.DateTime(), nullable=True))
    op.add_column("leads", sa.Column("resolution", sa.Text(), nullable=True))
    op.add_column("leads", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("leads", sa.Column("closed_at", sa.DateTime(), nullable=True))
    op.create_foreign_key("fk_leads_case", "leads", "cases", ["case_id"], ["case_id"])
    op.create_foreign_key("fk_leads_assigned_user", "leads", "users", ["assigned_to_user_id"], ["user_id"])
    op.create_index("ix_leads_assignee_status", "leads", ["assigned_to_user_id", "status"])
    op.execute("UPDATE leads SET status = 'new' WHERE status IS NULL")
    op.alter_column("leads", "status", nullable=False)
    op.execute("UPDATE leads SET updated_at = created_at WHERE updated_at IS NULL")
    op.alter_column("leads", "updated_at", nullable=False)
    op.alter_column("leads", "priority", server_default=None)


def downgrade():
    op.drop_index("ix_leads_assignee_status", table_name="leads")
    op.drop_constraint("fk_leads_assigned_user", "leads", type_="foreignkey")
    op.drop_constraint("fk_leads_case", "leads", type_="foreignkey")
    for column in ("closed_at", "updated_at", "resolution", "due_at", "assigned_to_user_id", "priority"):
        op.drop_column("leads", column)
