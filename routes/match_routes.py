from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.person import Person
from models.external_record import ExternalRecord
from models.match import Match
from models.user import User
from security.auth import require_role
from security.case_access import apply_related_case_access_filter
from security.tenant_scope import apply_person_agency_scope
from services.match_service import calculate_match_score
from services.job_queue import enqueue_job


router = APIRouter(

    prefix="/matches",

    tags=["Matches"]
)


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
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):

    persons = (
        apply_person_agency_scope(db.query(Person), current_user)
        .order_by(Person.created_at.desc())
        .limit(candidate_limit)
        .all()
    )

    records = apply_related_case_access_filter(
        db.query(ExternalRecord),
        ExternalRecord.case_id,
        current_user,
    )
    if current_user.role != "platform_admin":
        records = records.filter(ExternalRecord.agency_id == current_user.agency_id)
    records = records.order_by(ExternalRecord.created_at.desc()).limit(candidate_limit).all()


    results = []

    for person in persons:

        for record in records:

            score = calculate_match_score(person, record)


            if score >= 50:

                match = Match(

                    agency_id=(
                        current_user.agency_id
                        if current_user.role != "platform_admin"
                        else record.agency_id
                    ),

                    person_id=person.person_id,

                    external_record_id=record.id,

                    score=score,

                    status="pending_review"
                )

                db.add(match)

                results.append({

                    "person": f"{person.first_name} {person.last_name}",
                    "record": f"{record.first_name} {record.last_name}",
                    "score": score
                })

    db.commit()

    return {
        "matches_found": len(results),
        "matches": results
    }
