from sqlalchemy.orm import Session

from models.alerts import Alerts
from models.case import Cases
from services.notification_service import notify_assigned_investigator_of_alert

# ALERT SERVICE - FOR BUSINESS LOGIC RELATED TO ALERTS GENERATED FROM CASES OR EXTERNAL SOURCES

def create_alert(

    db: Session,

    case_id: int | None,

    person_id: int | None,

    recipient_agency_id: int | None,

    alert_type: str,

    title: str,

    description: str,

    severity: str = "medium",
):

    alert = Alerts(

        case_id=case_id,

        person_id=person_id,

        recipient_agency_id=recipient_agency_id,

        alert_type=alert_type,

        severity=severity,

        title=title,

        description=description,

        alert_status="active",
    )

    db.add(alert)
    db.flush()
    if case_id is not None:
        case = db.query(Cases).filter(
            Cases.case_id == case_id,
            Cases.agency_id == recipient_agency_id,
        ).first()
        if case is not None:
            notify_assigned_investigator_of_alert(
                db,
                case=case,
                alert_id=alert.alert_id,
                title=alert.title,
                severity=alert.severity,
            )
    db.commit()
    db.refresh(alert)

    return alert
