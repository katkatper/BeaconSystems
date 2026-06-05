from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from database.connection import get_db
from models.user import User
from schemas.user_schema import AdminPasswordReset, AdminUserCreate
from security.auth import hash_password, require_role
from services.activity_service import create_activity_log

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.post("/")
def create_user(
    data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    existing_user = db.query(User).filter(
        (User.username == data.username) | (User.email == data.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    admin_roles = ["admin", "agency_admin", "supervisor", "investigator", "analyst", "viewer"]
    supervisor_roles = ["supervisor", "investigator", "analyst", "viewer"]
    allowed_roles = admin_roles if current_user.role == "admin" else supervisor_roles

    if data.role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Invalid role for your permissions")

    agency_id = data.agency_id

    if current_user.role in {"agency_admin", "supervisor"}:
        agency_id = current_user.agency_id

    new_user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        agency_id=agency_id,
        is_active=True,
        password_changed_at=datetime.utcnow(),
        must_change_password=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="CREATE_USER",
        entity="user",
        entity_id=new_user.user_id,
        details=f"Created user {new_user.username} with role {new_user.role}",
    )

    return {
        "message": "User created",
        "user_id": new_user.user_id,
        "username": new_user.username,
        "role": new_user.role,
        "agency_id": new_user.agency_id,
    }


@router.get("/")
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    query = db.query(User)

    if current_user.role != "admin":
        query = query.filter(User.agency_id == current_user.agency_id)

    return query.order_by(User.username.asc()).all()


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

    allowed_roles = ["admin", "agency_admin", "supervisor", "investigator", "analyst", "viewer"]

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
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    query = db.query(User).filter(User.user_id == user_id)

    if current_user.role != "admin":
        query = query.filter(User.agency_id == current_user.agency_id)

    user = query.first()

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


@router.put("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    data: AdminPasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "agency_admin", "supervisor")),
):
    if len(data.temporary_password) < 12:
        raise HTTPException(
            status_code=400,
            detail="Temporary password must be at least 12 characters",
        )

    query = db.query(User).filter(User.user_id == user_id)

    if current_user.role != "admin":
        query = query.filter(User.agency_id == current_user.agency_id)

    user = query.first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role == "supervisor" and user.role in {"admin", "agency_admin"}:
        raise HTTPException(
            status_code=403,
            detail="Supervisors cannot reset admin account passwords",
        )

    user.password_hash = hash_password(data.temporary_password)
    user.password_changed_at = datetime.utcnow()
    user.must_change_password = True
    db.commit()
    db.refresh(user)

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="RESET_USER_PASSWORD",
        entity="user",
        entity_id=user.user_id,
        details=f"Reset password for user {user.username}",
    )

    return {
        "message": f"Temporary password set for {user.username}",
        "user_id": user.user_id,
        "must_change_password": user.must_change_password,
    }
