from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from models.bolo_alert import BoloAlert
from models.case import Cases
from models.user import User
from security.auth import get_current_user, require_role
from services.activity_service import create_activity_log


router = APIRouter(prefix="/bolos", tags=["BOLO Alerts"])


class BoloCreate(BaseModel):
    case_id: int
    title: str
    person_name: str | None = None
    last_known_location: str | None = None
    description: str
    risk_level: str = "high"
    share_with_partners: bool = False
    expires_at: datetime | None = None


class BoloUpdate(BaseModel):
    title: str | None = None
    person_name: str | None = None
    last_known_location: str | None = None
    description: str | None = None
    risk_level: str | None = None
    status: str | None = None
    share_with_partners: bool | None = None
    expires_at: datetime | None = None


def can_access_case(db: Session, case_id: int, current_user: User):
    query = db.query(Cases).filter(Cases.case_id == case_id)

    if current_user.role == "admin":
        case = query.first()
    elif current_user.role == "agency_admin":
        case = query.filter(Cases.agency_id == current_user.agency_id).first()
    elif current_user.role == "investigator":
        case = query.filter(
            Cases.agency_id == current_user.agency_id,
            Cases.investigator_id == current_user.user_id,
        ).first()
    else:
        case = None

    if not case:
        raise HTTPException(status_code=403, detail="Case access denied")

    return case


@router.get("/")
def list_bolos(
    status: str | None = "active",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(BoloAlert)

    if current_user.role != "admin":
        query = query.filter(BoloAlert.agency_id == current_user.agency_id)

    if status:
        query = query.filter(BoloAlert.status == status)

    return query.order_by(BoloAlert.created_at.desc()).all()


@router.post("/")
def create_bolo(
    data: BoloCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "investigator")),
):
    case = can_access_case(db, data.case_id, current_user)

    bolo = BoloAlert(
        case_id=data.case_id,
        agency_id=case.agency_id,
        created_by=current_user.user_id,
        title=data.title,
        person_name=data.person_name,
        last_known_location=data.last_known_location,
        description=data.description,
        risk_level=data.risk_level,
        share_with_partners=data.share_with_partners,
        expires_at=data.expires_at,
    )

    db.add(bolo)
    db.commit()
    db.refresh(bolo)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CREATE_BOLO",
        entity="bolo_alert",
        entity_id=bolo.bolo_id,
        details=f"Created BOLO alert: {bolo.title}",
    )

    return bolo


@router.put("/{bolo_id}")
def update_bolo(
    bolo_id: int,
    data: BoloUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "investigator")),
):
    query = db.query(BoloAlert).filter(BoloAlert.bolo_id == bolo_id)

    if current_user.role != "admin":
        query = query.filter(BoloAlert.agency_id == current_user.agency_id)

    bolo = query.first()

    if not bolo:
        raise HTTPException(status_code=404, detail="BOLO alert not found")

    if current_user.role == "investigator" and bolo.created_by != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only creator or supervisor can update this BOLO")

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(bolo, field, value)

    db.commit()
    db.refresh(bolo)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="UPDATE_BOLO",
        entity="bolo_alert",
        entity_id=bolo.bolo_id,
        details=f"Updated BOLO alert: {bolo.title}",
    )

    return bolo