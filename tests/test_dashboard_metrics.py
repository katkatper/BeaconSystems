from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.connection import Base
from models.agencies import Agencies  # noqa: F401
from models.case import Cases
from models.person import Person  # noqa: F401
from services.dashboard_metrics import load_case_dashboard_metrics


def test_case_dashboard_metrics_are_loaded_together():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[Agencies.__table__, Person.__table__, Cases.__table__],
    )
    now = datetime(2026, 10, 10, 12, 0, 0)

    with Session(engine) as session:
        session.add_all(
            [
                Cases(
                    case_number="A",
                    title="Critical active",
                    person_id=1,
                    agency_id=1,
                    case_status="open",
                    priority_level="critical",
                    updated_at=now - timedelta(days=15),
                ),
                Cases(
                    case_number="B",
                    title="High active",
                    person_id=2,
                    agency_id=1,
                    investigator_id=9,
                    case_status="OPEN",
                    priority_level="high",
                    updated_at=now - timedelta(days=8),
                ),
                Cases(
                    case_number="C",
                    title="Closed",
                    person_id=3,
                    agency_id=1,
                    case_status="closed",
                    priority_level="high",
                    updated_at=now - timedelta(days=30),
                ),
            ]
        )
        session.commit()

        metrics = load_case_dashboard_metrics(
            session.query(Cases),
            seven_days_ago=now - timedelta(days=7),
            fourteen_days_ago=now - timedelta(days=14),
            inactive_statuses=("closed", "resolved", "archived"),
        )

    assert metrics.total_cases == 3
    assert metrics.open_cases == 2
    assert metrics.high_priority_cases == 3
    assert metrics.critical_cases == 1
    assert metrics.high_risk_cases == 1
    assert metrics.inactive_7_days == 2
    assert metrics.inactive_14_days == 1
    assert metrics.unassigned_cases == 1
