from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.agencies import Agencies
from models.async_job import AsyncJob
from models.integration_source import IntegrationSource
from models.integration_source_agency import IntegrationSourceAgency
from routes.partner_intake_routes import PartnerIntakeBatch, PartnerIntakeCreate
from services.job_queue import complete_job, fail_job


def _provider_job(agency_id: int, source_id: int, key: str) -> AsyncJob:
    return AsyncJob(
        agency_id=agency_id,
        job_type="partner_intake.process",
        payload={"data": {"integration_source_id": source_id}},
        idempotency_key=key,
        status="running",
        priority=40,
        attempts=1,
        max_attempts=5,
        available_at=datetime(2026, 10, 31, 12, 0, 0),
    )


def test_provider_failures_open_circuit_and_success_resets_health():
    engine = create_engine("sqlite:///:memory:")
    Agencies.__table__.create(engine)
    IntegrationSource.__table__.create(engine)
    IntegrationSourceAgency.__table__.create(engine)
    AsyncJob.__table__.create(engine)
    db = sessionmaker(bind=engine)()
    now = datetime(2026, 10, 31, 12, 0, 0)
    agency = Agencies(agency_id=41, agency_name="Provider test agency")
    source = IntegrationSource(
        id=9,
        name="Test toll provider",
        source_type="toll",
        status="approved",
        is_active=True,
    )
    db.add_all([agency, source])
    db.commit()

    for index in range(5):
        job = _provider_job(agency.agency_id, source.id, f"provider:{index}")
        db.add(job)
        db.commit()
        fail_job(db, job, "provider unavailable", now=now + timedelta(seconds=index))

    db.refresh(source)
    assert source.consecutive_failures == 5
    assert source.circuit_open_until == now + timedelta(seconds=4, minutes=5)
    assert source.last_failure_reason == "provider unavailable"

    recovery = _provider_job(agency.agency_id, source.id, "provider:recovery")
    db.add(recovery)
    db.commit()
    complete_job(db, recovery, now=now + timedelta(minutes=6))
    db.refresh(source)
    assert source.consecutive_failures == 0
    assert source.circuit_open_until is None
    assert source.last_success_at == now + timedelta(minutes=6)
    db.close()
    engine.dispose()


def test_provider_batch_contract_is_bounded_and_homogeneous_inputs_are_valid():
    record = PartnerIntakeCreate(
        agency_id=41,
        integration_source_id=9,
        record_type="vehicle_observation",
        summary="Synthetic staging observation",
    )
    batch = PartnerIntakeBatch(records=[record, record.model_copy()])
    assert len(batch.records) == 2
