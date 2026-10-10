"""add phase one query indexes

Revision ID: 0a6f708294b1
Revises: fe5f60718293
"""

from alembic import op


revision = "0a6f708294b1"
down_revision = "fe5f60718293"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_cases_agency_status_updated", "cases", ["agency_id", "case_status", "updated_at"])
    op.create_index("ix_evidence_case_created", "evidence", ["case_id", "created_at"])
    op.create_index("ix_activity_log_agency_created", "activity_log", ["agency_id", "created_at"])
    op.create_index("ix_alerts_recipient_created", "alerts", ["recipient_agency_id", "created_at"])
    op.create_index("ix_bolo_alerts_agency_status_created", "bolo_alerts", ["agency_id", "status", "created_at"])
    op.create_index("ix_persons_status_created", "persons", ["status", "created_at"])


def downgrade():
    op.drop_index("ix_persons_status_created", table_name="persons")
    op.drop_index("ix_bolo_alerts_agency_status_created", table_name="bolo_alerts")
    op.drop_index("ix_alerts_recipient_created", table_name="alerts")
    op.drop_index("ix_activity_log_agency_created", table_name="activity_log")
    op.drop_index("ix_evidence_case_created", table_name="evidence")
    op.drop_index("ix_cases_agency_status_updated", table_name="cases")
