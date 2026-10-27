from types import SimpleNamespace

from sqlalchemy.orm import Session

from models.activity_log import ActivityLog
from models.integration_source import IntegrationSource
from models.partner_intake_record import PartnerIntakeRecord
from services.activity_service import create_activity_log
from services.job_handlers import register_job_handler


@register_job_handler("partner_intake.process")
def handle_partner_intake_job(db: Session, job) -> None:
    agency_id = int(job.payload["agency_id"])
    if agency_id != job.agency_id:
        raise ValueError("Job payload tenant does not match job owner")

    ingestion_key = str(job.payload["ingestion_key"])
    existing = db.query(PartnerIntakeRecord).filter(
        PartnerIntakeRecord.agency_id == agency_id,
        PartnerIntakeRecord.ingestion_key == ingestion_key,
    ).first()
    data = SimpleNamespace(**job.payload["data"])
    source = db.query(IntegrationSource).filter(
        IntegrationSource.id == data.integration_source_id,
        IntegrationSource.status == "approved",
        IntegrationSource.is_active.is_(True),
    ).first()
    if not source:
        raise ValueError("Partner source is not approved and active")

    if existing:
        intake = existing
    else:
        # Imported lazily to keep route registration independent from worker startup.
        from routes.partner_intake_routes import create_intake_record

        intake = create_intake_record(
            db=db,
            data=data,
            source=source,
            intake_channel="automated_async",
            received_by_user_id=None,
            agency_id=agency_id,
            ingestion_key=ingestion_key,
        )
    job.payload = {**job.payload, "intake_id": intake.intake_id}
    audit_exists = db.query(ActivityLog.id).filter(
        ActivityLog.agency_id == agency_id,
        ActivityLog.action == "PROCESS_ASYNC_PARTNER_INTAKE",
        ActivityLog.entity == "partner_intake_record",
        ActivityLog.entity_id == intake.intake_id,
    ).first()
    if not audit_exists:
        create_activity_log(
            db=db,
            user_id=None,
            agency_id=agency_id,
            action="PROCESS_ASYNC_PARTNER_INTAKE",
            entity="partner_intake_record",
            entity_id=intake.intake_id,
            details=(
                f"Queued partner intake processed from source {source.name}; "
                f"match score {intake.match_score or 0}"
            ),
        )
