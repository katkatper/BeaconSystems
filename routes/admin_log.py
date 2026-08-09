from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from database.connection import get_db
from models.activity_log import ActivityLog    
from security.auth import require_role, get_current_user
from models.user import User
from services.pagination import PaginationParams, paginate_query

router= APIRouter(prefix="/admin/Audit", tags=["Audit"])    

# ADMIN AUDIT LOG ROUTE - ONLY ACCESSIBLE TO ADMINS

@router.get("/")    
def get_audit_logs(
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
 logs = paginate_query(
     db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()),
     pagination,
     response,
 )

 return logs


