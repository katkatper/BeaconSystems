from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from models.user import User
from security.auth import require_role

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.get("/")
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    return db.query(User).all()


@router.put("/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    allowed_roles = ["admin", "agency_admin", "investigator", "analyst", "viewer"]

    if role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    user.role = role
    db.commit()
    db.refresh(user)

    return {
        "message": f"Updated {user.username} role to {role}",
        "user_id": user.user_id,
        "role": user.role,
    }


@router.put("/{user_id}/agency")
def update_user_agency(
    user_id: int,
    agency_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.agency_id = agency_id
    db.commit()
    db.refresh(user)

    return {
        "message": f"Updated {user.username} agency to {agency_id}",
        "user_id": user.user_id,
        "agency_id": user.agency_id,
    }


@router.put("/{user_id}/status")
def update_user_status(
    user_id: int,
    is_active: bool = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = is_active
    db.commit()
    db.refresh(user)

    return {
        "message": f"Updated {user.username} status",
        "user_id": user.user_id,
        "is_active": user.is_active,
    }