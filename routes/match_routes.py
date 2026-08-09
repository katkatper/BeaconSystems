from fastapi import APIRouter, Depends, Query
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


router = APIRouter(

    prefix="/matches",

    tags=["Matches"]
)


@router.post("/run")

def run_matching(
    candidate_limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin", "agency_admin", "supervisor")
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
    if current_user.role != "admin":
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
                        if current_user.role != "admin"
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
