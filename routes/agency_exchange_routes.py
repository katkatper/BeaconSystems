from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from models.agency_exchange import AgencyExchange
from models.case import Cases
from models.user import User
from security.auth import require_role
from security.case_access import accessible_case_ids
from services.activity_service import create_activity_log


router = APIRouter(prefix="/agency-exchanges", tags=["Agency Exchanges"])


class AgencyExchangeCreate(BaseModel):
    case_id: int
    from_agency: str
    to_agency: str
    information_type: str
    summary: str
    reason: str
    legal_authority: str | None = None


@router.get("/")
def list_agency_exchanges(
    case_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "investigator")),
):
    query = db.query(AgencyExchange)

    if case_id is not None:
        query = query.filter(AgencyExchange.case_id == case_id)

    if current_user.role == "agency_admin":
        query = (
            query
            .join(Cases, AgencyExchange.case_id == Cases.case_id)
            .filter(Cases.agency_id == current_user.agency_id)
        )

    if current_user.role == "investigator":
        allowed_case_ids = set(accessible_case_ids(db, current_user))

        if not allowed_case_ids:
            return []

        if case_id is not None and case_id not in allowed_case_ids:
            raise HTTPException(status_code=403, detail="Not authorized for this case exchange log")

        query = query.filter(AgencyExchange.case_id.in_(allowed_case_ids))

    return query.order_by(AgencyExchange.created_at.desc()).limit(50).all()


@router.post("/")
def create_agency_exchange(
    data: AgencyExchangeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin")),
):
    case = db.query(Cases).filter(Cases.case_id == data.case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if current_user.role != "admin" and case.agency_id != current_user.agency_id:
        raise HTTPException(status_code=403, detail="Cannot approve exchange for another agency")

    exchange = AgencyExchange(
        case_id=data.case_id,
        from_agency=data.from_agency,
        to_agency=data.to_agency,
        information_type=data.information_type,
        summary=data.summary,
        reason=data.reason,
        legal_authority=data.legal_authority,
        approved_by=current_user.user_id,
        status="approved",
    )

    db.add(exchange)
    db.commit()
    db.refresh(exchange)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="AGENCY_INFORMATION_EXCHANGE_APPROVED",
        entity="case",
        entity_id=data.case_id,
        details=(
            f"Approved agency exchange from {data.from_agency} to {data.to_agency}. "
            f"Reason: {data.reason}"
        ),
    )

    return {
        "message": "Agency information exchange recorded",
        "exchange_id": exchange.exchange_id,
        "case_id": exchange.case_id,
        "approved_by": exchange.approved_by,
    }
