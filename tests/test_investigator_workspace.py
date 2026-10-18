from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from database.connection import get_db
from models.agencies import Agencies
from models.alerts import Alerts
from models.case import Cases
from models.leads import Leads
from models.person import Person
from routes.dashboard_routes import router
from security.auth import get_current_user
from services.investigator_workspace import load_investigator_workspace


@pytest.fixture
def workspace_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for model in (Agencies, Person, Cases, Alerts, Leads):
        model.__table__.create(engine)
    with Session(engine) as db:
        for cid, agency, investigator, status in (
            (1, 10, 7, "Open"), (2, 10, 8, "Open"),
            (3, 11, 7, "Open"), (4, 10, 7, "Closed"),
            (5, 10, 7, "Open"),
        ):
            db.add(Cases(case_id=cid, case_number=f"C-{cid}", title=f"Case {cid}",
                agency_id=agency, investigator_id=investigator, person_id=1,
                case_status=status, priority_level="critical" if cid == 5 else "medium"))
            db.add(Alerts(alert_id=cid, case_id=cid, recipient_agency_id=agency,
                title=f"Alert {cid}", alert_status="active", severity="high"))
            db.add(Leads(lead_id=cid, case_id=cid, status="new"))
        db.add(Alerts(alert_id=99, case_id=1, recipient_agency_id=11,
            title="Wrong recipient", alert_status="active", severity="critical"))
        db.add(Leads(lead_id=99, case_id=1, status="resolved"))
        db.commit()
        yield db
    engine.dispose()


def investigator(**overrides):
    return SimpleNamespace(**({"user_id": 7, "agency_id": 10, "role": "investigator", "is_active": True} | overrides))


def test_workspace_excludes_other_users_tenants_and_closed_cases(workspace_db):
    result = load_investigator_workspace(workspace_db, investigator())
    assert [row["case_id"] for row in result["assigned_cases"]] == [5, 1]
    assert {row["alert_id"] for row in result["urgent_alerts"]} == {1, 5}
    assert {row["lead_id"] for row in result["pending_leads"]} == {1, 5}
    assert not any(result["has_more"].values())


def test_workspace_is_bounded_and_indicates_more(workspace_db):
    result = load_investigator_workspace(workspace_db, investigator(), limit=1)
    assert all(result["has_more"].values())
    assert all(len(result[key]) == 1 for key in result["has_more"])
    with pytest.raises(ValueError):
        load_investigator_workspace(workspace_db, investigator(), limit=1000)


def test_workspace_empty_state(workspace_db):
    result = load_investigator_workspace(workspace_db, investigator(user_id=999))
    assert result["assigned_cases"] == result["urgent_alerts"] == result["pending_leads"] == []


@pytest.mark.parametrize("role,active,expected", [("investigator", True, 200), ("viewer", True, 403), ("investigator", False, 403)])
def test_workspace_endpoint_checks_role_and_activity(workspace_db, role, active, expected):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: workspace_db
    app.dependency_overrides[get_current_user] = lambda: investigator(role=role, is_active=active)
    with TestClient(app) as client:
        response = client.get("/dashboard/investigator")
        assert response.status_code == expected
        if expected == 200:
            assert {row["case_id"] for row in response.json()["assigned_cases"]} == {1, 5}
