from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.connection import Base
from models.agencies import Agencies
from models.case import Cases
from models.external_record import ExternalRecord
from models.match import Match
from models.person import Person
from services.matching_jobs import run_agency_matching


def test_matching_prefilters_candidates_and_remains_idempotent():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[
            Agencies.__table__,
            Person.__table__,
            Cases.__table__,
            ExternalRecord.__table__,
            Match.__table__,
        ],
    )

    with Session(engine) as session:
        session.add(Agencies(agency_id=10, agency_name="Test Agency"))
        session.add_all(
            [
                Person(
                    person_id=1,
                    first_name="Jane",
                    last_name="Doe",
                    age=31,
                    last_seen_location="North Toll Plaza",
                ),
                Person(
                    person_id=2,
                    first_name="Unrelated",
                    last_name="Person",
                    age=55,
                ),
            ]
        )
        session.add_all(
            [
                Cases(
                    case_id=1,
                    case_number="MP-1",
                    title="Jane Doe",
                    person_id=1,
                    agency_id=10,
                ),
                Cases(
                    case_id=2,
                    case_number="MP-2",
                    title="Unrelated Person",
                    person_id=2,
                    agency_id=10,
                ),
            ]
        )
        session.add_all(
            [
                ExternalRecord(
                    id=1,
                    agency_id=10,
                    record_type="hospital_encounter",
                    first_name="Jane",
                    last_name="Doe",
                    age=31,
                    location="North Toll Plaza",
                ),
                ExternalRecord(
                    id=2,
                    agency_id=10,
                    record_type="unrelated",
                    first_name="Different",
                    last_name="Subject",
                    age=77,
                ),
            ]
        )
        session.commit()

        assert run_agency_matching(session, agency_id=10, candidate_limit=200) == 1
        session.commit()
        assert run_agency_matching(session, agency_id=10, candidate_limit=200) == 0
        assert session.query(Match).count() == 1

    engine.dispose()
