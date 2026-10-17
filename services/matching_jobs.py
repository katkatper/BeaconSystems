from sqlalchemy.orm import Session

from models.case import Cases
from models.external_record import ExternalRecord
from models.match import Match
from models.person import Person
from services.job_handlers import register_job_handler
from services.match_service import calculate_match_score


def run_agency_matching(db: Session, *, agency_id: int, candidate_limit: int) -> int:
    persons = (
        db.query(Person)
        .join(Cases, Cases.person_id == Person.person_id)
        .filter(Cases.agency_id == agency_id)
        .order_by(Person.created_at.desc())
        .limit(candidate_limit)
        .all()
    )
    records = (
        db.query(ExternalRecord)
        .filter(ExternalRecord.agency_id == agency_id)
        .order_by(ExternalRecord.created_at.desc())
        .limit(candidate_limit)
        .all()
    )

    created = 0
    for person in persons:
        for record in records:
            score = calculate_match_score(person, record)
            if score < 50:
                continue
            exists = db.query(Match.id).filter(
                Match.agency_id == agency_id,
                Match.person_id == person.person_id,
                Match.external_record_id == record.id,
            ).first()
            if exists:
                continue
            db.add(
                Match(
                    agency_id=agency_id,
                    person_id=person.person_id,
                    external_record_id=record.id,
                    score=score,
                    status="pending_review",
                )
            )
            created += 1
    db.flush()
    return created


@register_job_handler("matching.run")
def handle_matching_job(db: Session, job) -> None:
    agency_id = int(job.payload["agency_id"])
    if agency_id != job.agency_id:
        raise ValueError("Job payload tenant does not match job owner")
    candidate_limit = max(1, min(int(job.payload.get("candidate_limit", 200)), 500))
    created = run_agency_matching(
        db,
        agency_id=agency_id,
        candidate_limit=candidate_limit,
    )
    job.payload = {**job.payload, "matches_created": created}
