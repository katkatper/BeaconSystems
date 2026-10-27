from sqlalchemy.orm import Session

from models.case import Cases
from models.external_record import ExternalRecord
from models.match import Match
from models.person import Person
from services.job_handlers import register_job_handler
from services.match_service import calculate_match_score


def _normalized(value) -> str:
    return str(value or "").strip().lower()


def run_agency_matching(db: Session, *, agency_id: int, candidate_limit: int) -> int:
    persons = (
        db.query(Person)
        .filter(
            Person.person_id.in_(
                db.query(Cases.person_id).filter(Cases.agency_id == agency_id)
            )
        )
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

    record_indexes: dict[tuple[str, object], set[int]] = {}
    records_by_id = {record.id: record for record in records}
    for record in records:
        for field, value in (
            ("first_name", _normalized(record.first_name)),
            ("last_name", _normalized(record.last_name)),
            ("age", record.age),
        ):
            if value not in (None, ""):
                record_indexes.setdefault((field, value), set()).add(record.id)

    person_ids = [person.person_id for person in persons]
    record_ids = list(records_by_id)
    existing_pairs = set()
    if person_ids and record_ids:
        existing_pairs = {
            (person_id, record_id)
            for person_id, record_id in db.query(
                Match.person_id,
                Match.external_record_id,
            ).filter(
                Match.agency_id == agency_id,
                Match.person_id.in_(person_ids),
                Match.external_record_id.in_(record_ids),
            ).all()
        }

    created = 0
    for person in persons:
        candidate_ids: set[int] = set()
        for key in (
            ("first_name", _normalized(person.first_name)),
            ("last_name", _normalized(person.last_name)),
            ("age", person.age),
        ):
            if key[1] not in (None, ""):
                candidate_ids.update(record_indexes.get(key, set()))
        for record_id in candidate_ids:
            record = records_by_id[record_id]
            score = calculate_match_score(person, record)
            if score < 50:
                continue
            pair = (person.person_id, record.id)
            if pair in existing_pairs:
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
            existing_pairs.add(pair)
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
