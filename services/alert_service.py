from sqlalchemy.orm import Session
from models.alerts import Alerts


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
    db.commit()
    db.refresh(alert)

    return alert