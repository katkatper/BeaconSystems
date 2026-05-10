from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from models.alerts import Alerts
from  database.connection import get_db

# ALERTS ROUTES - FOR MANAGING ALERTS GENERATED FROM CASES OR EXTERNAL SOURCES


router=APIRouter()

router = APIRouter(

    prefix="/alerts",

    tags=["Alerts"]
)


@router.post("/")

def create_alerts(

    case_id: int,

    person_id: int,

    alert_type: str,

    title: str,

    description: str,

    severity: str = "medium",

    db: Session = Depends(get_db)
):


    alerts = Alerts(

        case_id=case_id,

        person_id=person_id, 

        alert_type=alert_type,

        title=title,

        description=description,

        severity=severity,
    )
    
    db.add(alerts)
    db.commit()
    db.refresh(alerts)


    return alerts


@router.get("/")

def get_alerts(

    db: Session = Depends(get_db)
):


    return db.query(Alerts).order_by(

        Alerts.created_at.desc()

    ).all()