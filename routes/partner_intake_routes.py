from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from config.settings import PARTNER_WEBHOOK_TOKEN
from database.connection import get_db
from database.tenant_context import configure_tenant_session
from models.agencies import Agencies
from models.bolo_alert import BoloAlert
from models.case import Cases
from models.external_record import ExternalRecord
from models.integration_source import IntegrationSource
from models.partner_intake_record import PartnerIntakeRecord
from models.person import Person
from models.timeline_events import Timeline_Event
from models.user import User
from security.auth import get_current_user, require_role, verify_password
from security.case_access import assert_case_write_access
from security.partner_tokens import is_partner_token_hash, verify_partner_token
from security.tenant_scope import apply_partner_intake_agency_scope
from services.activity_service import create_activity_log
from services.clock import utc_now
from services.geocoding_fields import apply_geocode_result, copy_geocode_fields
from services.geocoding_service import geocode_address
from services.job_queue import CapacityQuotaExceeded, enqueue_job
from services.pagination import PaginationParams, paginate_query
from services.partner_matching import (
    normalize_text,
    score_bolo_vehicle_match,
    score_case_match,
    split_subject_name,
)
from services.provider_observations import normalize_provider_payload

router = APIRouter(prefix="/partner-intake", tags=["Partner Intake"])


class PartnerIntakeCreate(BaseModel):
    agency_id: Optional[int] = None
    integration_source_id: int
    record_type: str
    external_id: Optional[str] = None
    subject_name: Optional[str] = None
    location: Optional[str] = None
    summary: str
    raw_data: dict[str, Any] | None = None


class PartnerIntakeAttach(BaseModel):
    case_id: int
    person_id: Optional[int] = None
    review_notes: Optional[str] = None
    legal_authority_type: str
    legal_authority_reference: Optional[str] = None
    legal_authority_notes: Optional[str] = None


class PartnerIntakeReview(BaseModel):
    review_notes: Optional[str] = None


LEGAL_AUTHORITY_TYPES = {
    "consent",
    "subpoena",
    "search_warrant",
    "court_order",
    "wiretap_order",
    "emergency_disclosure",
    "partner_agreement",
    "other",
}


def authenticate_partner_source(source: IntegrationSource, token: str | None) -> None:
    if source.webhook_secret_hash:
        if not token:
            valid_token = False
        elif is_partner_token_hash(source.webhook_secret_hash):
            valid_token = verify_partner_token(token, source.webhook_secret_hash)
        else:
            # Credentials created before the HMAC migration remain valid until
            # the source token is next rotated.
            valid_token = verify_password(token, source.webhook_secret_hash)
        if not valid_token:
            raise HTTPException(status_code=401, detail="Invalid partner webhook token")
        return
    if not PARTNER_WEBHOOK_TOKEN:
        raise HTTPException(status_code=503, detail="Partner webhook token is not configured")
    if token != PARTNER_WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid partner webhook token")


def authorize_partner_destination(source: IntegrationSource, agency_id: int) -> None:
    authorized_agencies = [item.agency_id for item in source.authorized_agencies]
    if source.webhook_secret_hash and not authorized_agencies:
        raise HTTPException(
            status_code=403,
            detail="Partner source has no authorized destination agencies",
        )
    if authorized_agencies and agency_id not in authorized_agencies:
        raise HTTPException(
            status_code=403,
            detail="Partner source is not authorized for the destination agency",
        )


def apply_geocode_fields(target, geocoded: dict[str, Any] | None) -> None:
    apply_geocode_result(target, geocoded)


def copy_intake_geocode_fields(external_record: ExternalRecord, intake: PartnerIntakeRecord) -> None:
    copy_geocode_fields(external_record, intake)


def find_best_case_match(
    db: Session,
    data: PartnerIntakeCreate,
    agency_id: int,
    canonical_data: dict[str, Any],
    match_threshold: int,
):
    best_match = None
    best_bolo = None
    best_score = 0
    best_reasons: list[str] = []

    subject_name = canonical_data.get("subject_name") or data.subject_name
    first_name, last_name = split_subject_name(subject_name)
    case_query = db.query(Cases).join(Person).filter(Cases.agency_id == agency_id)
    identity_filters = []
    if first_name:
        identity_filters.append(func.lower(Person.first_name) == first_name.lower())
    if last_name:
        identity_filters.append(func.lower(Person.last_name) == last_name.lower())
    age = (data.raw_data or {}).get("age")
    if not identity_filters and age not in (None, ""):
        try:
            identity_filters.append(Person.age == int(age))
        except (TypeError, ValueError):
            identity_filters = []
    cases = (
        case_query.filter(*identity_filters).limit(100).all()
        if identity_filters
        else []
    )

    for case in cases:
        score, reasons = score_case_match(case, data)

        if score > best_score:
            best_match = case
            best_score = score
            best_reasons = reasons

    bolo_query = db.query(BoloAlert).filter(
        BoloAlert.agency_id == agency_id,
        BoloAlert.status == "active",
        or_(BoloAlert.expires_at.is_(None), BoloAlert.expires_at > utc_now()),
    )
    plate_number = canonical_data.get("plate_number")
    if plate_number:
        bolo_query = bolo_query.filter(BoloAlert.plate_number == plate_number)
        plate_state = canonical_data.get("plate_state")
        if plate_state:
            bolo_query = bolo_query.filter(
                or_(BoloAlert.plate_state == plate_state, BoloAlert.plate_state.is_(None))
            )
    else:
        vehicle_filters = []
        for column, field in (
            (BoloAlert.vehicle_make, "vehicle_make"),
            (BoloAlert.vehicle_model, "vehicle_model"),
            (BoloAlert.vehicle_color, "vehicle_color"),
        ):
            value = canonical_data.get(field)
            if value not in (None, ""):
                vehicle_filters.append(func.lower(column) == str(value).lower())
        vehicle_year = canonical_data.get("vehicle_year")
        if vehicle_year not in (None, ""):
            vehicle_filters.append(BoloAlert.vehicle_year == int(vehicle_year))
        bolo_query = (
            bolo_query.filter(*vehicle_filters)
            if vehicle_filters
            else bolo_query.filter(BoloAlert.bolo_id == -1)
        )
    active_bolos = bolo_query.limit(100).all()
    for bolo in active_bolos:
        score, reasons = score_bolo_vehicle_match(bolo, canonical_data)
        if score > best_score:
            best_match = next((case for case in cases if case.case_id == bolo.case_id), None)
            if best_match is None:
                best_match = db.query(Cases).filter(
                    Cases.case_id == bolo.case_id,
                    Cases.agency_id == agency_id,
                ).first()
            best_bolo = bolo
            best_score = score
            best_reasons = reasons

    if not best_match or best_score < match_threshold:
        return None, None, best_score, "No match met the configured review threshold"

    return best_match, best_bolo, best_score, "; ".join(best_reasons)


def create_intake_record(
    *,
    db: Session,
    data: PartnerIntakeCreate,
    source: IntegrationSource,
    intake_channel: str,
    received_by_user_id: int | None,
    agency_id: int,
    ingestion_key: str | None = None,
):
    if ingestion_key:
        existing = db.query(PartnerIntakeRecord).filter(
            PartnerIntakeRecord.agency_id == agency_id,
            PartnerIntakeRecord.ingestion_key == ingestion_key,
        ).first()
        if existing:
            return existing
    if source.allowed_record_types and data.record_type not in source.allowed_record_types:
        raise HTTPException(
            status_code=400,
            detail="Record type is not authorized for this partner source",
        )

    try:
        canonical_data = normalize_provider_payload(
            data.raw_data or {},
            source.field_mapping,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Provider payload could not be normalized: {exc}",
        ) from exc
    if data.subject_name and not canonical_data.get("subject_name"):
        canonical_data["subject_name"] = data.subject_name
    if data.location and not canonical_data.get("location"):
        canonical_data["location"] = data.location

    matched_case, matched_bolo, match_score, match_reason = find_best_case_match(
        db,
        data,
        agency_id,
        canonical_data,
        source.match_threshold or 60,
    )
    status = "matched_pending_review" if matched_case else "pending_review"
    provider_latitude = canonical_data.get("latitude")
    provider_longitude = canonical_data.get("longitude")
    geocoded = (
        None
        if provider_latitude is not None and provider_longitude is not None
        else geocode_address(data.location)
    )

    intake = PartnerIntakeRecord(
        agency_id=agency_id,
        integration_source_id=data.integration_source_id,
        received_by_user_id=received_by_user_id,
        suggested_case_id=matched_case.case_id if matched_case else None,
        suggested_person_id=matched_case.person_id if matched_case else None,
        suggested_bolo_id=matched_bolo.bolo_id if matched_bolo else None,
        record_type=data.record_type,
        external_id=data.external_id,
        ingestion_key=ingestion_key,
        subject_name=data.subject_name,
        location=data.location,
        latitude=provider_latitude,
        longitude=provider_longitude,
        geocode_provider="partner" if provider_latitude is not None else None,
        geocode_accuracy="provider_supplied" if provider_latitude is not None else None,
        summary=data.summary,
        raw_data=data.raw_data,
        canonical_data=canonical_data,
        schema_version="1.0",
        match_score=match_score,
        match_reason=match_reason,
        match_case_status=matched_case.case_status if matched_case else None,
        intake_channel=intake_channel,
        status=status,
    )
    if geocoded:
        apply_geocode_fields(intake, geocoded)

    db.add(intake)
    db.commit()
    db.refresh(intake)

    return intake


@router.post("/automated-async", status_code=202)
def queue_automated_partner_intake_record(
    data: PartnerIntakeCreate,
    db: Session = Depends(get_db),
    x_beacon_partner_token: Optional[str] = Header(None),
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=8,
        max_length=160,
    ),
):
    source = get_approved_source(db, data.integration_source_id)
    authenticate_partner_source(source, x_beacon_partner_token)
    if data.agency_id is None:
        raise HTTPException(
            status_code=400,
            detail="Automated partner intake must identify its destination agency",
        )
    authorize_partner_destination(source, data.agency_id)
    if not db.query(Agencies).filter(Agencies.agency_id == data.agency_id).first():
        raise HTTPException(status_code=404, detail="Agency not found")

    configure_tenant_session(db, agency_id=data.agency_id, platform_admin=False)
    ingestion_key = f"partner:{data.integration_source_id}:{idempotency_key}"
    try:
        job, created = enqueue_job(
            db,
            agency_id=data.agency_id,
            job_type="partner_intake.process",
            payload={
                "agency_id": data.agency_id,
                "ingestion_key": ingestion_key,
                "data": data.model_dump(mode="json"),
            },
            idempotency_key=ingestion_key,
            priority=40,
        )
    except CapacityQuotaExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    db.commit()
    db.refresh(job)
    return {"job_id": job.job_id, "status": job.status, "created": created}


def get_approved_source(db: Session, source_id: int):
    source = db.query(IntegrationSource).filter(
        IntegrationSource.id == source_id
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Partner source not found")

    if source.status != "approved" or not source.is_active:
        raise HTTPException(
            status_code=400,
            detail="Partner source must be approved and active before intake",
        )

    return source


def serialize_partner_intake(intake: PartnerIntakeRecord) -> dict[str, Any]:
    return {
        "intake_id": intake.intake_id,
        "agency_id": intake.agency_id,
        "integration_source_id": intake.integration_source_id,
        "received_by_user_id": intake.received_by_user_id,
        "reviewed_by_user_id": intake.reviewed_by_user_id,
        "attached_external_record_id": intake.attached_external_record_id,
        "suggested_case_id": intake.suggested_case_id,
        "suggested_person_id": intake.suggested_person_id,
        "suggested_bolo_id": intake.suggested_bolo_id,
        "record_type": intake.record_type,
        "external_id": intake.external_id,
        "subject_name": intake.subject_name,
        "location": intake.location,
        "latitude": intake.latitude,
        "longitude": intake.longitude,
        "geocode_provider": intake.geocode_provider,
        "geocode_accuracy": intake.geocode_accuracy,
        "geocode_score": intake.geocode_score,
        "geocoded_address": intake.geocoded_address,
        "geocoded_at": intake.geocoded_at,
        "summary": intake.summary,
        "raw_data": intake.raw_data,
        "canonical_data": intake.canonical_data,
        "schema_version": intake.schema_version,
        "match_score": intake.match_score,
        "match_reason": intake.match_reason,
        "match_case_status": intake.match_case_status,
        "intake_channel": intake.intake_channel,
        "legal_authority_type": intake.legal_authority_type,
        "legal_authority_reference": intake.legal_authority_reference,
        "legal_authority_notes": intake.legal_authority_notes,
        "status": intake.status,
        "review_notes": intake.review_notes,
        "received_at": intake.received_at,
        "reviewed_at": intake.reviewed_at,
    }


@router.get("/")
def list_partner_intake_records(
    status: Optional[str] = None,
    agency_id: Optional[int] = None,
    response: Response = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = apply_partner_intake_agency_scope(
        db.query(PartnerIntakeRecord),
        current_user,
    )

    if current_user.role == "platform_admin" and agency_id is not None:
        query = query.filter(PartnerIntakeRecord.agency_id == agency_id)

    if status:
        query = query.filter(PartnerIntakeRecord.status == status)
    else:
        query = query.filter(
            PartnerIntakeRecord.status.in_(
                ["pending_review", "matched_pending_review"]
            )
        )

    records = paginate_query(
        query.order_by(PartnerIntakeRecord.received_at.desc()),
        pagination,
        response,
    )
    return [serialize_partner_intake(record) for record in records]


@router.post("/")
def receive_partner_intake_record(
    data: PartnerIntakeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "agency_admin")),
):
    source = get_approved_source(db, data.integration_source_id)
    agency_id = current_user.agency_id if current_user.role != "platform_admin" else data.agency_id

    if agency_id is None:
        raise HTTPException(status_code=400, detail="Select an agency for this intake")

    if not db.query(Agencies).filter(Agencies.agency_id == agency_id).first():
        raise HTTPException(status_code=404, detail="Agency not found")

    intake = create_intake_record(
        db=db,
        data=data,
        source=source,
        intake_channel="manual",
        received_by_user_id=current_user.user_id,
        agency_id=agency_id,
    )

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="RECEIVE_PARTNER_INTAKE",
        entity="partner_intake_record",
        entity_id=intake.intake_id,
        details=(
            f"Partner intake received from source {source.name}: "
            f"{intake.record_type}; match score {intake.match_score or 0}"
        ),
    )

    return serialize_partner_intake(intake)


@router.post("/automated", status_code=202, deprecated=True)
def receive_automated_partner_intake_record(
    data: PartnerIntakeCreate,
    db: Session = Depends(get_db),
    x_beacon_partner_token: Optional[str] = Header(None),
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=8,
        max_length=160,
    ),
):
    return queue_automated_partner_intake_record(
        data=data,
        db=db,
        x_beacon_partner_token=x_beacon_partner_token,
        idempotency_key=idempotency_key,
    )


@router.put("/{intake_id}/attach")
def attach_partner_intake_to_case(
    intake_id: int,
    data: PartnerIntakeAttach,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
):
    intake = apply_partner_intake_agency_scope(
        db.query(PartnerIntakeRecord).filter(
            PartnerIntakeRecord.intake_id == intake_id
        ),
        current_user,
    ).first()

    if not intake:
        raise HTTPException(status_code=404, detail="Partner intake record not found")

    if intake.status == "attached":
        raise HTTPException(status_code=400, detail="Partner intake already attached")

    legal_authority_type = normalize_text(data.legal_authority_type)
    if legal_authority_type not in LEGAL_AUTHORITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Select a valid legal authority before attaching partner data",
        )

    target_case = assert_case_write_access(db, data.case_id, current_user)
    if intake.agency_id != target_case.agency_id:
        raise HTTPException(status_code=404, detail="Partner intake record not found")

    if data.person_id is not None and data.person_id != target_case.person_id:
        raise HTTPException(
            status_code=400,
            detail="Selected person is not the subject of the target case",
        )
    first_name, last_name = split_subject_name(intake.subject_name)
    reviewed_at = datetime.utcnow()
    linked_raw_data = dict(intake.raw_data or {})
    linked_raw_data["beacon_canonical_observation"] = intake.canonical_data or {}
    linked_raw_data["beacon_legal_authority"] = {
        "type": legal_authority_type,
        "reference": data.legal_authority_reference,
        "notes": data.legal_authority_notes,
        "reviewed_by_user_id": current_user.user_id,
        "reviewed_at": reviewed_at.isoformat(),
    }

    external_record = ExternalRecord(
        agency_id=target_case.agency_id,
        integration_source_id=intake.integration_source_id,
        record_type=intake.record_type,
        external_id=intake.external_id,
        first_name=first_name,
        last_name=last_name,
        location=intake.location,
        notes=intake.summary,
        raw_data=linked_raw_data,
        person_id=data.person_id or target_case.person_id,
        case_id=data.case_id,
    )
    copy_intake_geocode_fields(external_record, intake)
    if intake.location and (external_record.latitude is None or external_record.longitude is None):
        apply_geocode_fields(external_record, geocode_address(intake.location))

    db.add(external_record)
    db.commit()
    db.refresh(external_record)

    timeline_event = Timeline_Event(
        case_id=data.case_id,
        person_id=data.person_id or target_case.person_id,
        event_type="partner_intake_attached",
        source_type=intake.record_type,
        location=intake.location,
        description=intake.summary,
    )
    db.add(timeline_event)

    intake.status = "attached"
    intake.reviewed_by_user_id = current_user.user_id
    intake.review_notes = data.review_notes
    intake.reviewed_at = reviewed_at
    intake.attached_external_record_id = external_record.id
    intake.legal_authority_type = legal_authority_type
    intake.legal_authority_reference = data.legal_authority_reference
    intake.legal_authority_notes = data.legal_authority_notes

    db.commit()
    db.refresh(intake)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="ATTACH_PARTNER_INTAKE_TO_CASE",
        entity="partner_intake_record",
        entity_id=intake.intake_id,
        details=(
            f"Partner intake {intake.intake_id} attached to case {data.case_id}; "
            f"legal authority: {legal_authority_type}"
        ),
    )

    return serialize_partner_intake(intake)


@router.put("/{intake_id}/dismiss")
def dismiss_partner_intake_record(
    intake_id: int,
    data: PartnerIntakeReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
):
    intake = apply_partner_intake_agency_scope(
        db.query(PartnerIntakeRecord).filter(
            PartnerIntakeRecord.intake_id == intake_id
        ),
        current_user,
    ).first()

    if not intake:
        raise HTTPException(status_code=404, detail="Partner intake record not found")

    intake.status = "dismissed"
    intake.reviewed_by_user_id = current_user.user_id
    intake.review_notes = data.review_notes
    intake.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(intake)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="DISMISS_PARTNER_INTAKE",
        entity="partner_intake_record",
        entity_id=intake.intake_id,
        details=f"Partner intake {intake.intake_id} dismissed",
    )

    return serialize_partner_intake(intake)
