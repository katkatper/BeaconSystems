from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.settings import PARTNER_WEBHOOK_TOKEN
from database.connection import get_db
from models.IntegrationSource import IntegrationSource
from models.case import Cases
from models.external_record import ExternalRecord
from models.partner_intake_record import PartnerIntakeRecord
from models.person import Person
from models.timeline_events import Timeline_Event
from models.user import User
from security.auth import get_current_user, require_role
from security.case_access import assert_case_write_access
from services.activity_service import create_activity_log


router = APIRouter(prefix="/partner-intake", tags=["Partner Intake"])


class PartnerIntakeCreate(BaseModel):
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


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


def text_tokens(value: str) -> set[str]:
    normalized = "".join(
        character if character.isalnum() else " "
        for character in normalize_text(value)
    )
    return {
        token
        for token in normalized.split()
        if len(token) > 2
        and token not in {"the", "and", "for", "with", "near", "from"}
    }


def split_subject_name(subject_name: str | None):
    if not subject_name:
        return None, None

    parts = subject_name.strip().split()

    if len(parts) == 1:
        return parts[0], None

    return parts[0], " ".join(parts[1:])


def score_case_match(case: Cases, data: PartnerIntakeCreate) -> tuple[int, list[str]]:
    person = case.person
    raw_data = data.raw_data or {}
    score = 0
    reasons: list[str] = []

    subject = normalize_text(data.subject_name)
    summary = normalize_text(data.summary)
    location = normalize_text(data.location)
    raw_blob = normalize_text(raw_data)
    search_blob = " ".join([subject, summary, location, raw_blob])

    first_name = normalize_text(person.first_name if person else "")
    last_name = normalize_text(person.last_name if person else "")
    full_name = " ".join(part for part in [first_name, last_name] if part)

    if full_name and full_name in search_blob:
        score += 45
        reasons.append("full name matched")
    else:
        if first_name and first_name in search_blob:
            score += 18
            reasons.append("first name matched")
        if last_name and last_name in search_blob:
            score += 25
            reasons.append("last name matched")

    partner_age = raw_data.get("age") if isinstance(raw_data, dict) else None
    if partner_age and person and person.age and int(partner_age) == int(person.age):
        score += 12
        reasons.append("age matched")

    for label, value in [
        ("eye color", person.eye_color if person else None),
        ("hair color", person.hair_color if person else None),
        ("risk level", person.risk_level if person else None),
    ]:
        normalized_value = normalize_text(value)
        if normalized_value and normalized_value in search_blob:
            score += 8
            reasons.append(f"{label} matched")

    case_locations = " ".join(
        normalize_text(value)
        for value in [
            case.last_seen_location,
            person.last_seen_location if person else "",
        ]
    )
    location_overlap = text_tokens(location).intersection(text_tokens(case_locations))
    if location_overlap:
        score += min(15, len(location_overlap) * 5)
        reasons.append("location overlapped")

    case_context = " ".join(
        normalize_text(value)
        for value in [
            case.case_number,
            case.title,
            case.description,
            case.notes,
            person.description if person else "",
            person.scars if person else "",
            person.tattoos if person else "",
            person.medical_conditions if person else "",
        ]
    )
    keyword_overlap = text_tokens(summary).intersection(text_tokens(case_context))
    if keyword_overlap:
        score += min(20, len(keyword_overlap) * 4)
        reasons.append("description keywords overlapped")

    if normalize_text(case.case_status) in {"closed", "cold"}:
        reasons.append(f"{case.case_status.lower()} case considered")

    return min(score, 100), reasons


def find_best_case_match(db: Session, data: PartnerIntakeCreate):
    best_match = None
    best_score = 0
    best_reasons: list[str] = []

    cases = db.query(Cases).join(Person).all()

    for case in cases:
        score, reasons = score_case_match(case, data)

        if score > best_score:
            best_match = case
            best_score = score
            best_reasons = reasons

    if not best_match or best_score < 35:
        return None, 0, "No strong case match found"

    return best_match, best_score, "; ".join(best_reasons)


def create_intake_record(
    *,
    db: Session,
    data: PartnerIntakeCreate,
    source: IntegrationSource,
    intake_channel: str,
    received_by_user_id: int | None,
):
    matched_case, match_score, match_reason = find_best_case_match(db, data)
    status = "matched_pending_review" if matched_case else "pending_review"

    intake = PartnerIntakeRecord(
        integration_source_id=data.integration_source_id,
        received_by_user_id=received_by_user_id,
        suggested_case_id=matched_case.case_id if matched_case else None,
        suggested_person_id=matched_case.person_id if matched_case else None,
        record_type=data.record_type,
        external_id=data.external_id,
        subject_name=data.subject_name,
        location=data.location,
        summary=data.summary,
        raw_data=data.raw_data,
        match_score=match_score,
        match_reason=match_reason,
        match_case_status=matched_case.case_status if matched_case else None,
        intake_channel=intake_channel,
        status=status,
    )

    db.add(intake)
    db.commit()
    db.refresh(intake)

    return intake


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
        "integration_source_id": intake.integration_source_id,
        "received_by_user_id": intake.received_by_user_id,
        "reviewed_by_user_id": intake.reviewed_by_user_id,
        "attached_external_record_id": intake.attached_external_record_id,
        "suggested_case_id": intake.suggested_case_id,
        "suggested_person_id": intake.suggested_person_id,
        "record_type": intake.record_type,
        "external_id": intake.external_id,
        "subject_name": intake.subject_name,
        "location": intake.location,
        "summary": intake.summary,
        "raw_data": intake.raw_data,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(PartnerIntakeRecord)

    if status:
        query = query.filter(PartnerIntakeRecord.status == status)
    else:
        query = query.filter(
            PartnerIntakeRecord.status.in_(
                ["pending_review", "matched_pending_review"]
            )
        )

    records = query.order_by(PartnerIntakeRecord.received_at.desc()).all()
    return [serialize_partner_intake(record) for record in records]


@router.post("/")
def receive_partner_intake_record(
    data: PartnerIntakeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin")),
):
    source = get_approved_source(db, data.integration_source_id)
    intake = create_intake_record(
        db=db,
        data=data,
        source=source,
        intake_channel="manual",
        received_by_user_id=current_user.user_id,
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


@router.post("/automated")
def receive_automated_partner_intake_record(
    data: PartnerIntakeCreate,
    db: Session = Depends(get_db),
    x_beacon_partner_token: Optional[str] = Header(None),
):
    if not PARTNER_WEBHOOK_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Partner webhook token is not configured",
        )

    if x_beacon_partner_token != PARTNER_WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid partner webhook token")

    source = get_approved_source(db, data.integration_source_id)
    intake = create_intake_record(
        db=db,
        data=data,
        source=source,
        intake_channel="automated",
        received_by_user_id=None,
    )

    create_activity_log(
        db=db,
        user_id=None,
        agency_id=None,
        action="AUTOMATED_PARTNER_INTAKE",
        entity="partner_intake_record",
        entity_id=intake.intake_id,
        details=(
            f"Automated partner intake received from source {source.name}: "
            f"{intake.record_type}; match score {intake.match_score or 0}"
        ),
    )

    return serialize_partner_intake(intake)


@router.put("/{intake_id}/attach")
def attach_partner_intake_to_case(
    intake_id: int,
    data: PartnerIntakeAttach,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "investigator")),
):
    intake = db.query(PartnerIntakeRecord).filter(
        PartnerIntakeRecord.intake_id == intake_id
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

    assert_case_write_access(db, data.case_id, current_user)
    first_name, last_name = split_subject_name(intake.subject_name)
    reviewed_at = datetime.utcnow()
    linked_raw_data = dict(intake.raw_data or {})
    linked_raw_data["beacon_legal_authority"] = {
        "type": legal_authority_type,
        "reference": data.legal_authority_reference,
        "notes": data.legal_authority_notes,
        "reviewed_by_user_id": current_user.user_id,
        "reviewed_at": reviewed_at.isoformat(),
    }

    external_record = ExternalRecord(
        integration_source_id=intake.integration_source_id,
        record_type=intake.record_type,
        external_id=intake.external_id,
        first_name=first_name,
        last_name=last_name,
        location=intake.location,
        notes=intake.summary,
        raw_data=linked_raw_data,
        person_id=data.person_id,
        case_id=data.case_id,
    )

    db.add(external_record)
    db.commit()
    db.refresh(external_record)

    timeline_event = Timeline_Event(
        case_id=data.case_id,
        person_id=data.person_id,
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
    current_user: User = Depends(require_role("admin", "agency_admin", "investigator")),
):
    intake = db.query(PartnerIntakeRecord).filter(
        PartnerIntakeRecord.intake_id == intake_id
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
