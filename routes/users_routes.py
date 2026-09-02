import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Response
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from config.settings import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from database.connection import get_db
from models.user import User
from schemas.user_schema import MfaEnable, MfaLoginVerify, PasswordChange, UserCreate, UserLogin, UserResponse, UserRoleUpdate
from security.auth import hash_password, verify_password, create_access_token, require_role, get_current_user
from services.activity_service import create_activity_log
from services.pagination import PaginationParams, paginate_query

router = APIRouter(prefix="/users", tags=["Users"])

PASSWORD_ROTATION_DAYS = 120
MFA_ISSUER = "Beacon"
MFA_STEP_SECONDS = 30
MFA_DIGITS = 6


def password_expiration_for(user: User):
    password_changed_at = user.password_changed_at or user.created_at or datetime.utcnow()
    password_expires_at = password_changed_at + timedelta(days=PASSWORD_ROTATION_DAYS)
    password_change_required = user.must_change_password or datetime.utcnow() >= password_expires_at

    return password_change_required, password_expires_at


def generate_mfa_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8").rstrip("=")


def normalized_mfa_secret(secret: str) -> str:
    return secret + ("=" * (-len(secret) % 8))


def generate_totp(secret: str, for_time: Optional[float] = None) -> str:
    key = base64.b32decode(normalized_mfa_secret(secret), casefold=True)
    counter = int((for_time or time.time()) // MFA_STEP_SECONDS)
    message = struct.pack(">Q", counter)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF

    return str(code % (10 ** MFA_DIGITS)).zfill(MFA_DIGITS)


def verify_totp(secret: Optional[str], code: str) -> bool:
    if not secret:
        return False

    clean_code = "".join(character for character in code if character.isdigit())

    if len(clean_code) != MFA_DIGITS:
        return False

    now = time.time()

    for window in range(-1, 2):
        expected = generate_totp(secret, now + (window * MFA_STEP_SECONDS))

        if hmac.compare_digest(expected, clean_code):
            return True

    return False


def build_login_response(user: User, password_change_required: bool, password_expires_at: datetime):
    session_expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token({
        "sub": user.username,
        "user_id": user.user_id,
        "role": user.role,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
        "agency_id": user.agency_id,
        "mfa_enabled": bool(user.mfa_enabled),
        "password_change_required": password_change_required,
        "password_expires_at": password_expires_at.isoformat(),
        "session_expires_at": f"{session_expires_at.isoformat()}Z",
    }


def verify_mfa_login_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA challenge")

    if payload.get("purpose") != "mfa":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA challenge")

    username = payload.get("sub")

    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA challenge")

    return username


def mfa_otpauth_uri(user: User) -> str:
    account = quote(f"{MFA_ISSUER}:{user.username}")
    issuer = quote(MFA_ISSUER)

    return f"otpauth://totp/{account}?secret={user.mfa_secret}&issuer={issuer}&digits={MFA_DIGITS}&period={MFA_STEP_SECONDS}"

# USER ROUTES WITH ACTIVITY LOGGING

@router.post("/register")
def register_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("platform_admin", "agency_admin")
    ),
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
    role="investigator",
    agency_id=current_user.agency_id,
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


    password_change_required, password_expires_at = password_expiration_for(user)

    if user.mfa_enabled:
        mfa_token = create_access_token(
            {
                "sub": user.username,
                "user_id": user.user_id,
                "role": user.role,
                "purpose": "mfa",
            },
            expires_delta=timedelta(minutes=5),
        )

        create_activity_log(
            db=db,
            user_id=user.user_id,
            agency_id=user.agency_id,
            action="MFA_CHALLENGE",
            entity="user",
            entity_id=user.user_id,
            details=f"MFA challenge issued for {user.username}",
        )

        db.commit()

        return {
            "mfa_required": True,
            "mfa_token": mfa_token,
            "token_type": "mfa",
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "agency_id": user.agency_id,
            "password_change_required": password_change_required,
            "password_expires_at": password_expires_at.isoformat(),
        }

    user.last_login_at = datetime.utcnow()

    create_activity_log(

        db=db,

        user_id=user.user_id,

        action="LOGIN",

        entity="user",

        entity_id=user.user_id,

        details=f"User {user.username} logged in",

    )

    db.commit()

    return build_login_response(user, password_change_required, password_expires_at)


@router.get("/mfa/setup")
def get_mfa_setup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.mfa_secret:
        current_user.mfa_secret = generate_mfa_secret()
        db.commit()
        db.refresh(current_user)

    return {
        "enabled": bool(current_user.mfa_enabled),
        "secret": current_user.mfa_secret,
        "otpauth_uri": mfa_otpauth_uri(current_user),
        "issuer": MFA_ISSUER,
        "account": current_user.username,
    }


@router.post("/mfa/enable")
def enable_mfa(
    data: MfaEnable,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.mfa_secret:
        current_user.mfa_secret = generate_mfa_secret()

    if not verify_totp(current_user.mfa_secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")

    current_user.mfa_enabled = True
    current_user.mfa_verified_at = datetime.utcnow()

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="MFA_ENABLE",
        entity="user",
        entity_id=current_user.user_id,
        details=f"MFA enabled for {current_user.username}",
    )

    db.commit()

    return {"message": "MFA enabled", "mfa_enabled": True}


@router.post("/mfa/disable")
def disable_mfa(
    data: MfaEnable,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_totp(current_user.mfa_secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")

    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_verified_at = None

    create_activity_log(
        db=db,
        user_id=current_user.user_id,
        agency_id=current_user.agency_id,
        action="MFA_DISABLE",
        entity="user",
        entity_id=current_user.user_id,
        details=f"MFA disabled for {current_user.username}",
    )

    db.commit()

    return {"message": "MFA disabled", "mfa_enabled": False}


@router.post("/mfa/verify")
def verify_mfa_login(
    data: MfaLoginVerify,
    db: Session = Depends(get_db)
):
    username = verify_mfa_login_token(data.mfa_token)
    user = db.query(User).filter(User.username == username).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    if not verify_totp(user.mfa_secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")

    password_change_required, password_expires_at = password_expiration_for(user)
    user.last_login_at = datetime.utcnow()
    user.mfa_verified_at = datetime.utcnow()

    create_activity_log(
        db=db,
        user_id=user.user_id,
        agency_id=user.agency_id,
        action="LOGIN",
        entity="user",
        entity_id=user.user_id,
        details=f"User {user.username} logged in with MFA",
    )

    db.commit()

    return build_login_response(user, password_change_required, password_expires_at)


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

    response: Response,

    pagination: PaginationParams = Depends(),

    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):


    users = paginate_query(
        db.query(User).order_by(User.username.asc()),
        pagination,
        response,
    )

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        action="VIEW_USERS",

        entity="user",

        details=f"{current_user.username} viewed all users",
    )

    return users
