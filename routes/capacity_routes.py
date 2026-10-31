from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from models.agencies import Agencies
from models.user import User
from security.auth import require_role
from services.capacity_usage import agency_capacity_usage
from services.clock import utc_now

router = APIRouter(prefix="/operations/capacity", tags=["Operations Capacity"])


@router.get("/{agency_id}")
def get_agency_capacity(
    agency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin", "supervisor")
    ),
):
    if current_user.role != "platform_admin" and current_user.agency_id != agency_id:
        raise HTTPException(status_code=403, detail="Agency access denied")
    agency = db.query(Agencies).filter(Agencies.agency_id == agency_id).first()
    if agency is None:
        raise HTTPException(status_code=404, detail="Agency not found")
    return agency_capacity_usage(db, agency, utc_now())
