from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from models.activity_log import ActivityLog    
from security.auth import require_role, get_current_user
from models.user import User

router= APIRouter(prefix="/admin/Audit", tags=["Audit"])    

# ADMIN AUDIT LOG ROUTE - ONLY ACCESSIBLE TO ADMINS

@router.get("/")    
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
 logs = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).all()

 return logs


