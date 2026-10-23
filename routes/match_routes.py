from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from database.connection import get_db
from models.external_record import ExternalRecord
from models.match import Match
from models.person import Person
from models.user import User
from security.auth import require_role
from services.activity_service import create_activity_log
from services.clock import utc_now_aware
from services.job_queue import enqueue_job
from services.matching_jobs import run_agency_matching
from services.pagination import PaginationParams, paginate_query

router = APIRouter(

    prefix="/matches",

    tags=["Matches"]
)

MATCH_DISPOSITIONS = {"confirmed", "rejected", "needs_more_information"}


class MatchDisposition(BaseModel):
    disposition: str
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def normalize(self):
        self.disposition = self.disposition.strip().lower()
        self.reason = self.reason.strip()
        if self.disposition not in MATCH_DISPOSITIONS:
            raise ValueError("Unsupported match disposition")
        return self


def scoped_matches(db: Session, current_user: User):
    query = db.query(Match)
    if current_user.role != "platform_admin":
        query = query.filter(Match.agency_id == current_user.agency_id)
    return query


def serialize_match(match: Match, person: Person | None, record: ExternalRecord | None, reviewer: User | None):
    return {
        "match_id": match.id,
        "agency_id": match.agency_id,
        "person_id": match.person_id,
        "person_name": f"{person.first_name} {person.last_name}".strip() if person else None,
        "external_record_id": match.external_record_id,
        "record_name": f"{record.first_name or ''} {record.last_name or ''}".strip() if record else None,
        "record_type": record.record_type if record else None,
        "record_location": record.location if record else None,
        "score": match.score,
        "status": match.status or "pending_review",
        "disposition_reason": match.disposition_reason,
        "reviewed_by_user_id": match.reviewed_by_user_id,
        "reviewed_by": reviewer.username if reviewer else None,
        "reviewed_at": match.reviewed_at,
        "created_at": match.created_at,
        "updated_at": match.updated_at,
    }


@router.get("/")
def list_matches(
    response: Response,
    match_status: str | None = Query(None, alias="status"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
):
    query = scoped_matches(db, current_user)
    if match_status:
        query = query.filter(Match.status == match_status.strip().lower())
    matches = paginate_query(
        query.order_by(Match.created_at.desc(), Match.id.desc()), pagination, response,
        cursor_column=Match.id,
    )
    person_ids = {item.person_id for item in matches if item.person_id}
    record_ids = {item.external_record_id for item in matches if item.external_record_id}
    reviewer_ids = {item.reviewed_by_user_id for item in matches if item.reviewed_by_user_id}
    people = {item.person_id: item for item in db.query(Person).filter(Person.person_id.in_(person_ids)).all()} if person_ids else {}
    records = {item.id: item for item in db.query(ExternalRecord).filter(ExternalRecord.id.in_(record_ids)).all()} if record_ids else {}
    reviewers = {item.user_id: item for item in db.query(User).filter(User.user_id.in_(reviewer_ids)).all()} if reviewer_ids else {}
    return [serialize_match(item, people.get(item.person_id), records.get(item.external_record_id), reviewers.get(item.reviewed_by_user_id)) for item in matches]


@router.put("/{match_id}/disposition")
def disposition_match(
    match_id: int,
    data: MatchDisposition,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin", "agency_admin", "supervisor", "investigator")),
):
    match = scoped_matches(db, current_user).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found or access denied")
    if match.status in {"confirmed", "rejected"} and current_user.role == "investigator":
        raise HTTPException(status_code=409, detail="A supervisor must reopen a final match decision")
    record = db.query(ExternalRecord).filter(
        ExternalRecord.id == match.external_record_id,
        ExternalRecord.agency_id == match.agency_id,
    ).first()
    person = db.query(Person).filter(Person.person_id == match.person_id).first()
    if not record or not person:
        raise HTTPException(status_code=409, detail="Match source records are unavailable")
    match.status = data.disposition
    match.disposition_reason = data.reason
    match.reviewed_by_user_id = current_user.user_id
    match.reviewed_at = utc_now_aware()
    match.updated_at = match.reviewed_at
    if data.disposition == "confirmed" and record.person_id is None:
        record.person_id = person.person_id
    db.commit()
    db.refresh(match)
    create_activity_log(
        db=db, user_id=current_user.user_id, agency_id=match.agency_id,
        action="DISPOSITION_MATCH", entity="match", entity_id=match.id,
        details=f"{current_user.username} marked match {match.id} {match.status}: {data.reason}",
        ip_address=request.client.host if request.client else None,
    )
    return serialize_match(match, person, record, current_user)


@router.post("/run-async", status_code=status.HTTP_202_ACCEPTED)
def queue_matching(
    candidate_limit: int = Query(200, ge=1, le=500),
    agency_id: int | None = Query(None),
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=8,
        max_length=200,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):
    target_agency_id = current_user.agency_id
    if current_user.role == "platform_admin":
        target_agency_id = agency_id
    elif agency_id is not None and agency_id != current_user.agency_id:
        raise HTTPException(status_code=404, detail="Agency not found")

    if target_agency_id is None:
        raise HTTPException(status_code=400, detail="Select an agency for matching")

    job, created = enqueue_job(
        db,
        agency_id=target_agency_id,
        job_type="matching.run",
        payload={
            "agency_id": target_agency_id,
            "candidate_limit": candidate_limit,
            "requested_by_user_id": current_user.user_id,
        },
        idempotency_key=f"matching:{idempotency_key}",
        priority=10,
    )
    db.commit()
    db.refresh(job)
    return {
        "job_id": job.job_id,
        "status": job.status,
        "created": created,
    }


@router.post("/run")

def run_matching(
    candidate_limit: int = Query(200, ge=1, le=500),
    agency_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):
    target_agency_id = current_user.agency_id
    if current_user.role == "platform_admin":
        target_agency_id = agency_id
    elif agency_id is not None and agency_id != current_user.agency_id:
        raise HTTPException(status_code=404, detail="Agency not found")

    if target_agency_id is None:
        raise HTTPException(status_code=400, detail="Select an agency for matching")

    created = run_agency_matching(
        db,
        agency_id=target_agency_id,
        candidate_limit=candidate_limit,
    )
    db.commit()
    return {"matches_found": created, "agency_id": target_agency_id}
