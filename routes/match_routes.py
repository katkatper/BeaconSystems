from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from models.person import Person
from models.external_record import ExternalRecord
from models.match import Match
from services.match_service import calculate_match_score


router = APIRouter(

    prefix="/matches",

    tags=["Matches"]
)


@router.post("/run")

def run_matching(db: Session = Depends(get_db)):

    persons = db.query(Person).all()

    records = db.query(ExternalRecord).all()


    results = []

    for person in persons:

        for record in records:

            score = calculate_match_score(person, record)


            if score >= 50:

                match = Match(

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