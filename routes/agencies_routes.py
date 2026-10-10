from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from database.connection import get_db
from models.agencies import Agencies
from models.user import User
from schemas.agency_schema import AgencyResponse
from security.auth import get_current_user
from security.tenant_scope import apply_agency_directory_scope
from services.pagination import PaginationParams, paginate_query


router = APIRouter(prefix="/agencies", tags=["Agencies"])


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
