from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database.connection import get_db
from models.user import User
from schemas.user_schema import PasswordChange, UserCreate, UserLogin, UserResponse, UserRoleUpdate
from security.auth import hash_password, verify_password, create_access_token, require_role, get_current_user
from services.activity_service import create_activity_log

router = APIRouter(prefix="/users", tags=["Users"])

PASSWORD_ROTATION_DAYS = 120

# USER ROUTES WITH ACTIVITY LOGGING

@router.post("/register")

def register_user(

    data: UserCreate,

    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(

        (User.username == data.username) |

        (User.email == data.email)

    ).first()


    if existing_user:

        raise HTTPException(status_code=400, detail="User already exists")


    new_user = User(

        username=data.username,

        email=data.email,

        password_hash=hash_password(data.password),

        role="admin",

        password_changed_at=datetime.utcnow(),

        must_change_password=False,
    )


    db.add(new_user)

    db.commit()

    db.refresh(new_user)


    create_activity_log(

        db=db,

        user_id=new_user.user_id,

        action="REGISTER",

        entity="user",

        entity_id=new_user.user_id,

        details=f"User {new_user.username} registered",
    )


    return {"message": "User created"}


# LOGIN ROUTE WITH ACTIVITY LOGGING

@router.post("/login")

def login(

    data: UserLogin,

    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.username == data.username).first()


    if not user or not verify_password(data.password, user.password_hash):

        raise HTTPException(status_code=401, detail="Invalid credentials")


    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")


    password_changed_at = user.password_changed_at or user.created_at or datetime.utcnow()

    password_expires_at = password_changed_at + timedelta(days=PASSWORD_ROTATION_DAYS)

    password_change_required = user.must_change_password or datetime.utcnow() >= password_expires_at


    token = create_access_token({

        "sub": user.username,

        "user_id": user.user_id,

        "role": user.role
    })

    create_activity_log(

        db=db,

        user_id=user.user_id,

        action="LOGIN",

        entity="user",

        entity_id=user.user_id,

        details=f"User {user.username} logged in",

    )


    return {
        "access_token": token,

        "token_type": "bearer",

        "user_id": user.user_id,

        "username": user.username,

        "role": user.role,

        "agency_id": user.agency_id,

        "password_change_required": password_change_required,

        "password_expires_at": password_expires_at.isoformat(),
    }


@router.put("/change-password")

def change_password(

    data: PasswordChange,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    if not verify_password(data.current_password, current_user.password_hash):

        raise HTTPException(status_code=400, detail="Current password is incorrect")


    if len(data.new_password) < 12:

        raise HTTPException(status_code=400, detail="New password must be at least 12 characters")


    current_user.password_hash = hash_password(data.new_password)

    current_user.password_changed_at = datetime.utcnow()

    current_user.must_change_password = False

    db.commit()

    db.refresh(current_user)


    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        agency_id=current_user.agency_id,

        action="PASSWORD_CHANGE",

        entity="user",

        entity_id=current_user.user_id,

        details=f"User {current_user.username} changed password",
    )


    return {"message": "Password updated"}

# UPDATE USER ROLE ROUTE WITH ROLE-BASED ACCESS CONTROL AND ACTIVITY LOGGING


@router.put("/{user_id}/role")

def update_user_role(

    user_id: int,

    data: UserRoleUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin"))
):
    user = db.query(User).filter(User.user_id == user_id).first()


    if not user:
        raise HTTPException(status_code=404, detail="User not found")


    allowed_roles = ["admin", "agency_admin", "supervisor", "investigator", "analyst", "viewer"]


    if data.role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Invalid role")


    old_role = user.role

    user.role = data.role


    db.commit()

    db.refresh(user)


    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        action="ROLE_UPDATE",

        entity="user",

        entity_id=user.user_id,

        details=f"Changed {user.username} role from {old_role} to {data.role}",

    )

    return {
        "message": "User role updated",

        "user_id": user.user_id,

        "username": user.username,

        "role": user.role,
    }

# ACTIVATE USER ROUTE WITH ROLE-BASED ACCESS CONTROL AND ACTIVITY LOGGING

@router.put("/{user_id}/deactivate")

def deactivate_user(

    user_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin"))
):

    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")


    if user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="You cannot deactivate yourself")


    user.is_active = False

    db.commit()

    db.refresh(user)


    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        action="DEACTIVATE_USER",

        entity="user",

        entity_id=user.user_id,

        details=f"Deactivated user {user.username}",
    )

    return {
        "message": "User deactivated",

        "user_id": user.user_id,

        "username": user.username,

        "is_active": user.is_active,
    }



@router.put("/{user_id}/activate")

def activate_user(

    user_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin"))
):


    user = db.query(User).filter(User.user_id == user_id).first()


    if not user:
        raise HTTPException(status_code=404, detail="User not found")


    user.is_active = True

    db.commit()

    db.refresh(user)

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        action="ACTIVATE_USER",

        entity="user",

        entity_id=user.user_id,

        details=f"Activated user {user.username}",
    )


    return {
        "message": "User activated",

        "user_id": user.user_id,

        "username": user.username,

        "is_active": user.is_active,
    }


# GET ALL USERS ROUTE WITH ROLE-BASED ACCESS CONTROL AND ACTIVITY LOGGING(ADMIN ONLY)


@router.get("/", response_model=list[UserResponse])

def get_users(

    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):


    users = db.query(User).all()

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        action="VIEW_USERS",

        entity="user",

        details=f"{current_user.username} viewed all users",
    )

    return users
