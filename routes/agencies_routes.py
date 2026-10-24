from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from database.connection import get_db
from models.agencies import Agencies
from models.user import User
from schemas.agency_schema import AgencyCreate, AgencyResponse, AgencyStatusUpdate
from security.auth import get_current_user, require_role
from security.tenant_scope import apply_agency_directory_scope
from services.activity_service import create_activity_log
from services.agency_lifecycle import set_agency_status
from services.pagination import PaginationParams, paginate_query

router = APIRouter(prefix="/agencies", tags=["Agencies"])


@router.post("/", response_model=AgencyResponse, status_code=201)
def create_agency(
    data: AgencyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin")),
):
    name = data.agency_name.strip()
    existing = db.query(Agencies).filter(Agencies.agency_name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Agency already exists")
    agency = Agencies(
        **data.model_dump(exclude={"agency_name"}),
        agency_name=name,
        lifecycle_status="active",
    )
    db.add(agency)
    db.commit()
    db.refresh(agency)
    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=agency.agency_id,
        action="CREATE_AGENCY",
        entity="agency",
        entity_id=agency.agency_id,
        details=f"Created agency {agency.agency_name}",
        ip_address=request.client.host if request.client else None,
    )
    return agency


@router.patch("/{agency_id}/status")
def update_agency_status(
    agency_id: int,
    data: AgencyStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("platform_admin")),
):
    agency = db.query(Agencies).filter(Agencies.agency_id == agency_id).first()
    if agency is None:
        raise HTTPException(status_code=404, detail="Agency not found")
    affected_users = set_agency_status(db, current_user, agency, data.status, data.reason)
    db.commit()
    db.refresh(agency)
    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=agency.agency_id,
        action=f"AGENCY_{agency.lifecycle_status.upper()}",
        entity="agency",
        entity_id=agency.agency_id,
        details=f"Agency status changed; reason: {data.reason.strip()}",
        ip_address=request.client.host if request.client else None,
    )
    return {
        "agency_id": agency.agency_id,
        "status": agency.lifecycle_status,
        "affected_users": affected_users,
    }


@router.get("/", response_model=list[AgencyResponse])
def get_agencies(
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the agency directory allowed for the authenticated tenant."""
    query = apply_agency_directory_scope(db.query(Agencies), current_user)
    query = query.order_by(Agencies.agency_id.desc())
    return paginate_query(
        query,
        pagination,
        response,
        cursor_column=Agencies.agency_id,
    )
