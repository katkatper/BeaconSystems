import base64
import hashlib
import hmac
import secrets
import struct
import time
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Response
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from config.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
    IS_PRODUCTION,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)
from database.connection import get_db
from models.user import User
from models.auth_session import AuthSession
from schemas.user_schema import MfaEnable, MfaLoginVerify, PasswordChange, UserCreate, UserLogin, UserResponse, UserRoleUpdate
from security.auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
    hash_password,
    oauth2_scheme,
    require_role,
    verify_password,
)
from security.user_management import (
    USER_MANAGER_ROLES,
    apply_user_management_scope,
    assert_role_assignment_access,
    assert_user_management_access,
)
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


def build_login_response(
    db: Session,
    user: User,
    request: Request,
    response: Response,
    password_change_required: bool,
    password_expires_at: datetime,
):
    session_expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = secrets.token_urlsafe(48)
    session_id = str(uuid.uuid4())
    db.add(AuthSession(
        session_id=session_id,
        user_id=user.user_id,
        expires_at=session_expires_at,
        last_seen_at=datetime.utcnow(),
        ip_address=request.client.host if request.client else None,
        user_agent=(request.headers.get("user-agent") or "")[:512] or None,
        refresh_token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
        refresh_expires_at=refresh_expires_at,
    ))
    db.commit()
    token = create_access_token({
        "sub": str(user.user_id),
        "username": user.username,
        "role": user.role,
        "auth_version": user.auth_version,
        "sid": session_id,
    })
    response.set_cookie(
        key="beacon_refresh",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="strict",
        path="/users",
    )

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


def verify_mfa_login_token(token: str) -> tuple[int, int]:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        user_id = int(payload.get("sub"))
        auth_version = int(payload.get("auth_version"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA challenge")

    if payload.get("token_type") != "mfa" or user_id <= 0 or auth_version < 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA challenge")

    return user_id, auth_version


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

    request: Request,

    response: Response,

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
                "sub": str(user.user_id),
                "username": user.username,
                "role": user.role,
                "auth_version": user.auth_version,
            },
            expires_delta=timedelta(minutes=5),
            token_type="mfa",
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

    return build_login_response(db, user, request, response, password_change_required, password_expires_at)


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
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    user_id, auth_version = verify_mfa_login_token(data.mfa_token)
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user or not user.is_active or user.auth_version != auth_version:
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

    return build_login_response(db, user, request, response, password_change_required, password_expires_at)


@router.post("/refresh")
def refresh_session(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("beacon_refresh")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh session is unavailable")

    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    auth_session = db.query(AuthSession).filter(
        AuthSession.refresh_token_hash == token_hash,
        AuthSession.revoked_at.is_(None),
        AuthSession.refresh_expires_at > datetime.utcnow(),
    ).first()
    if not auth_session:
        response.delete_cookie("beacon_refresh", path="/users")
        raise HTTPException(status_code=401, detail="Refresh session is invalid")

    user = db.query(User).filter(User.user_id == auth_session.user_id).first()
    if not user or not user.is_active:
        auth_session.revoked_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=401, detail="User not found or inactive")

    rotated_token = secrets.token_urlsafe(48)
    auth_session.refresh_token_hash = hashlib.sha256(rotated_token.encode()).hexdigest()
    auth_session.last_seen_at = datetime.utcnow()
    db.commit()
    response.set_cookie(
        key="beacon_refresh", value=rotated_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True, secure=IS_PRODUCTION, samesite="strict", path="/users",
    )
    return {
        "access_token": create_access_token({
            "sub": str(user.user_id), "username": user.username,
            "role": user.role, "auth_version": user.auth_version,
            "sid": auth_session.session_id,
        }),
        "token_type": "bearer",
        "session_expires_at": f"{(datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()}Z",
    }


@router.post("/logout")
def logout(
    response: Response,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        session_id = str(decode_access_token(token).get("sid") or "")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    auth_session = db.query(AuthSession).filter(
        AuthSession.session_id == session_id,
        AuthSession.user_id == current_user.user_id,
        AuthSession.revoked_at.is_(None),
    ).first()
    if auth_session:
        auth_session.revoked_at = datetime.utcnow()
        db.commit()

    response.delete_cookie("beacon_refresh", path="/users")

    return {"message": "Logged out"}


def current_session_id(token: str) -> str:
    try:
        return str(decode_access_token(token).get("sid") or "")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")


@router.get("/sessions")
def list_sessions(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    active_session_id = current_session_id(token)
    sessions = db.query(AuthSession).filter(
        AuthSession.user_id == current_user.user_id,
        AuthSession.revoked_at.is_(None),
        AuthSession.refresh_expires_at > datetime.utcnow(),
    ).order_by(AuthSession.last_seen_at.desc()).all()
    return [{
        "session_id": item.session_id,
        "created_at": item.created_at,
        "last_seen_at": item.last_seen_at,
        "expires_at": item.refresh_expires_at,
        "ip_address": item.ip_address,
        "user_agent": item.user_agent,
        "is_current": item.session_id == active_session_id,
    } for item in sessions]


@router.post("/sessions/{session_id}/revoke")
def revoke_session(
    session_id: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_session = db.query(AuthSession).filter(
        AuthSession.session_id == session_id,
        AuthSession.user_id == current_user.user_id,
        AuthSession.revoked_at.is_(None),
    ).first()
    if not auth_session:
        raise HTTPException(status_code=404, detail="Active session not found")
    auth_session.revoked_at = datetime.utcnow()
    db.commit()
    return {"message": "Session revoked", "current_session": session_id == current_session_id(token)}


@router.post("/sessions/revoke-others")
def revoke_other_sessions(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    active_session_id = current_session_id(token)
    sessions = db.query(AuthSession).filter(
        AuthSession.user_id == current_user.user_id,
        AuthSession.session_id != active_session_id,
        AuthSession.revoked_at.is_(None),
    ).all()
    now = datetime.utcnow()
    for item in sessions:
        item.revoked_at = now
    db.commit()
    return {"message": "Other sessions revoked", "revoked_count": len(sessions)}


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

    current_user.auth_version += 1

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

    current_user: User = Depends(require_role(*USER_MANAGER_ROLES))
):
    user = db.query(User).filter(User.user_id == user_id).first()


    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    assert_user_management_access(current_user, user)
    assert_role_assignment_access(current_user, data.role)


    old_role = user.role

    user.role = data.role

    user.auth_version += 1


    db.commit()

    db.refresh(user)


    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        agency_id=current_user.agency_id,

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

    current_user: User = Depends(require_role(*USER_MANAGER_ROLES))
):

    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    assert_user_management_access(current_user, user)

    if user.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="You cannot deactivate yourself")


    user.is_active = False

    user.auth_version += 1

    db.commit()

    db.refresh(user)


    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        agency_id=current_user.agency_id,

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

    current_user: User = Depends(require_role(*USER_MANAGER_ROLES))
):


    user = db.query(User).filter(User.user_id == user_id).first()


    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    assert_user_management_access(current_user, user)

    user.is_active = True

    user.auth_version += 1

    db.commit()

    db.refresh(user)

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        agency_id=current_user.agency_id,

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
    current_user: User = Depends(require_role(*USER_MANAGER_ROLES))
):


    users = paginate_query(
        apply_user_management_scope(
            db.query(User),
            current_user,
        ).order_by(User.username.asc()),
        pagination,
        response,
    )

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        agency_id=current_user.agency_id,

        action="VIEW_USERS",

        entity="user",

        details=f"{current_user.username} viewed all users",
    )

    return users
