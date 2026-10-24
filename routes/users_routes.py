
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    IS_PRODUCTION,
    JWT_AUDIENCE,
    JWT_ISSUER,
    LOGIN_RATE_LIMIT_ATTEMPTS,
    LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    MFA_ENFORCEMENT_ENABLED,
    MFA_RATE_LIMIT_ATTEMPTS,
    MFA_RATE_LIMIT_WINDOW_SECONDS,
    REFRESH_RATE_LIMIT_ATTEMPTS,
    REFRESH_RATE_LIMIT_WINDOW_SECONDS,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)
from database.connection import get_db
from database.tenant_context import configure_tenant_session
from models.auth_session import AuthSession
from models.user import User
from schemas.user_schema import (
    MfaEnable,
    MfaEnrollmentComplete,
    MfaEnrollmentStart,
    MfaLoginVerify,
    PasswordChange,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRoleUpdate,
)
from security.auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
    hash_password,
    oauth2_scheme,
    require_role,
    verify_password,
)
from security.csrf import validate_cookie_request_origin
from security.field_encryption import decrypt_mfa_secret, encrypt_mfa_secret
from security.mfa import (
    MFA_ISSUER,
    build_otpauth_uri,
    generate_mfa_secret,
    verify_totp,
)
from security.rate_limit import client_address, enforce_rate_limit
from security.sessions import (
    create_auth_session,
    refresh_token_hash,
    revoke_auth_session,
    rotate_refresh_token,
    serialize_auth_session,
)
from security.user_management import (
    USER_MANAGER_ROLES,
    apply_user_management_scope,
)
from services.activity_service import create_activity_log
from services.agency_lifecycle import agency_is_active
from services.clock import utc_now
from services.pagination import PaginationParams, paginate_query
from services.user_administration import (
    assign_user_role,
    get_managed_user,
    set_user_active,
)

router = APIRouter(prefix="/users", tags=["Users"])

PASSWORD_ROTATION_DAYS = 120


def password_expiration_for(user: User):
    now = utc_now()
    password_changed_at = user.password_changed_at or user.created_at or now
    password_expires_at = password_changed_at + timedelta(days=PASSWORD_ROTATION_DAYS)
    password_change_required = user.must_change_password or now >= password_expires_at

    return password_change_required, password_expires_at


def build_login_response(
    db: Session,
    user: User,
    request: Request,
    response: Response,
    password_change_required: bool,
    password_expires_at: datetime,
    *,
    mfa_authenticated: bool,
):
    auth_session, refresh_token = create_auth_session(
        user.user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        mfa_authenticated=mfa_authenticated,
    )
    db.add(auth_session)
    db.commit()
    token = create_access_token({
        "sub": str(user.user_id),
        "username": user.username,
        "role": user.role,
        "auth_version": user.auth_version,
        "sid": auth_session.session_id,
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
        "mfa_authenticated": mfa_authenticated,
        "password_change_required": password_change_required,
        "password_expires_at": password_expires_at.isoformat(),
        "session_expires_at": f"{auth_session.expires_at.isoformat()}Z",
    }


def verify_mfa_challenge_token(token: str, expected_type: str) -> tuple[int, int]:
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

    if payload.get("token_type") != expected_type or user_id <= 0 or auth_version < 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA challenge")

    return user_id, auth_version


def issue_mfa_challenge(user: User, token_type: str) -> str:
    return create_access_token(
        {
            "sub": str(user.user_id),
            "username": user.username,
            "role": user.role,
            "auth_version": user.auth_version,
        },
        expires_delta=timedelta(minutes=5),
        token_type=token_type,
    )


def mfa_otpauth_uri(user: User, secret: str) -> str:
    return build_otpauth_uri(user.username, secret)

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
    password_changed_at=utc_now(),
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
    enforce_rate_limit(
        request,
        namespace="login",
        identifier=f"{client_address(request)}:{data.username.strip().lower()}",
        limit=LOGIN_RATE_LIMIT_ATTEMPTS,
        window_seconds=LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    )

    user = db.query(User).filter(User.username == data.username).first()


    if not user or not verify_password(data.password, user.password_hash):

        raise HTTPException(status_code=401, detail="Invalid credentials")


    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    if not agency_is_active(db, user.agency_id):
        raise HTTPException(status_code=403, detail="Agency access is inactive")

    configure_tenant_session(
        db,
        agency_id=user.agency_id,
        platform_admin=user.role == "platform_admin",
    )


    password_change_required, password_expires_at = password_expiration_for(user)

    if user.mfa_enabled:
        mfa_token = issue_mfa_challenge(user, "mfa")

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

    if MFA_ENFORCEMENT_ENABLED:
        enrollment_token = issue_mfa_challenge(user, "mfa_enrollment")
        create_activity_log(
            db=db,
            user_id=user.user_id,
            agency_id=user.agency_id,
            action="MFA_ENROLLMENT_CHALLENGE",
            entity="user",
            entity_id=user.user_id,
            details=f"MFA enrollment required for {user.username}",
        )
        return {
            "mfa_enrollment_required": True,
            "mfa_token": enrollment_token,
            "token_type": "mfa_enrollment",
            "username": user.username,
        }

    user.last_login_at = utc_now()

    create_activity_log(

        db=db,

        user_id=user.user_id,

        action="LOGIN",

        entity="user",

        entity_id=user.user_id,

        details=f"User {user.username} logged in",

    )

    db.commit()

    return build_login_response(
        db, user, request, response, password_change_required,
        password_expires_at, mfa_authenticated=False,
    )


@router.post("/mfa/enrollment/start")
def start_mfa_enrollment(
    data: MfaEnrollmentStart,
    request: Request,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        request,
        namespace="mfa-enrollment",
        identifier=f"{client_address(request)}:{data.mfa_token}",
        limit=MFA_RATE_LIMIT_ATTEMPTS,
        window_seconds=MFA_RATE_LIMIT_WINDOW_SECONDS,
    )
    user_id, auth_version = verify_mfa_challenge_token(
        data.mfa_token, "mfa_enrollment"
    )
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.is_active or user.auth_version != auth_version:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    if user.mfa_enabled:
        raise HTTPException(status_code=409, detail="MFA is already enabled")
    configure_tenant_session(
        db, agency_id=user.agency_id, platform_admin=user.role == "platform_admin"
    )
    if not user.mfa_secret:
        secret = generate_mfa_secret()
        user.mfa_secret = encrypt_mfa_secret(secret)
        db.commit()
    else:
        secret, was_plaintext = decrypt_mfa_secret(user.mfa_secret)
        if was_plaintext:
            user.mfa_secret = encrypt_mfa_secret(secret)
            db.commit()
    return {
        "secret": secret,
        "otpauth_uri": mfa_otpauth_uri(user, secret),
        "issuer": MFA_ISSUER,
        "account": user.username,
    }


@router.post("/mfa/enrollment/complete")
def complete_mfa_enrollment(
    data: MfaEnrollmentComplete,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        request,
        namespace="mfa-enrollment",
        identifier=f"{client_address(request)}:{data.mfa_token}",
        limit=MFA_RATE_LIMIT_ATTEMPTS,
        window_seconds=MFA_RATE_LIMIT_WINDOW_SECONDS,
    )
    user_id, auth_version = verify_mfa_challenge_token(
        data.mfa_token, "mfa_enrollment"
    )
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.is_active or user.auth_version != auth_version:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    configure_tenant_session(
        db, agency_id=user.agency_id, platform_admin=user.role == "platform_admin"
    )
    if not user.mfa_secret:
        raise HTTPException(status_code=401, detail="MFA enrollment was not started")
    secret, was_plaintext = decrypt_mfa_secret(user.mfa_secret)
    if not verify_totp(secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    if was_plaintext:
        user.mfa_secret = encrypt_mfa_secret(secret)
    user.mfa_enabled = True
    user.mfa_verified_at = utc_now()
    user.last_login_at = utc_now()
    password_change_required, password_expires_at = password_expiration_for(user)
    create_activity_log(
        db=db,
        user_id=user.user_id,
        agency_id=user.agency_id,
        action="MFA_ENROLLMENT_COMPLETE",
        entity="user",
        entity_id=user.user_id,
        details=f"MFA enrollment completed for {user.username}",
        ip_address=request.client.host if request.client else None,
    )
    return build_login_response(
        db, user, request, response, password_change_required,
        password_expires_at, mfa_authenticated=True,
    )


@router.get("/mfa/setup")
def get_mfa_setup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.mfa_enabled:
        return {
            "enabled": True,
            "issuer": MFA_ISSUER,
            "account": current_user.username,
        }

    if not current_user.mfa_secret:
        secret = generate_mfa_secret()
        current_user.mfa_secret = encrypt_mfa_secret(secret)
        db.commit()
        db.refresh(current_user)
    else:
        secret, was_plaintext = decrypt_mfa_secret(current_user.mfa_secret)
        if was_plaintext:
            current_user.mfa_secret = encrypt_mfa_secret(secret)
            db.commit()

    return {
        "enabled": False,
        "secret": secret,
        "otpauth_uri": mfa_otpauth_uri(current_user, secret),
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
        current_user.mfa_secret = encrypt_mfa_secret(generate_mfa_secret())

    secret, was_plaintext = decrypt_mfa_secret(current_user.mfa_secret)
    if not verify_totp(secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")

    if was_plaintext:
        current_user.mfa_secret = encrypt_mfa_secret(secret)
    current_user.mfa_enabled = True
    current_user.mfa_verified_at = utc_now()

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
    if MFA_ENFORCEMENT_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="MFA cannot be disabled while enforcement is active",
        )
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA is not configured")

    secret, _ = decrypt_mfa_secret(current_user.mfa_secret)
    if not verify_totp(secret, data.code):
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
    enforce_rate_limit(
        request,
        namespace="mfa",
        identifier=f"{client_address(request)}:{data.mfa_token}",
        limit=MFA_RATE_LIMIT_ATTEMPTS,
        window_seconds=MFA_RATE_LIMIT_WINDOW_SECONDS,
    )
    user_id, auth_version = verify_mfa_challenge_token(data.mfa_token, "mfa")
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user or not user.is_active or user.auth_version != auth_version:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    configure_tenant_session(
        db,
        agency_id=user.agency_id,
        platform_admin=user.role == "platform_admin",
    )

    if not user.mfa_secret:
        raise HTTPException(status_code=401, detail="MFA is not configured")

    secret, was_plaintext = decrypt_mfa_secret(user.mfa_secret)
    if not verify_totp(secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")

    password_change_required, password_expires_at = password_expiration_for(user)
    user.last_login_at = utc_now()
    user.mfa_verified_at = utc_now()
    if was_plaintext:
        user.mfa_secret = encrypt_mfa_secret(secret)

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

    return build_login_response(
        db, user, request, response, password_change_required,
        password_expires_at, mfa_authenticated=True,
    )


@router.post("/refresh")
def refresh_session(request: Request, response: Response, db: Session = Depends(get_db)):
    validate_cookie_request_origin(request)
    enforce_rate_limit(
        request,
        namespace="refresh",
        identifier=client_address(request),
        limit=REFRESH_RATE_LIMIT_ATTEMPTS,
        window_seconds=REFRESH_RATE_LIMIT_WINDOW_SECONDS,
    )
    refresh_token = request.cookies.get("beacon_refresh")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh session is unavailable")

    now = utc_now()
    token_hash = refresh_token_hash(refresh_token)
    auth_session = db.query(AuthSession).filter(
        AuthSession.refresh_token_hash == token_hash,
        AuthSession.revoked_at.is_(None),
        AuthSession.refresh_expires_at > now,
    ).first()
    if not auth_session:
        response.delete_cookie("beacon_refresh", path="/users")
        raise HTTPException(status_code=401, detail="Refresh session is invalid")

    user = db.query(User).filter(User.user_id == auth_session.user_id).first()
    if not user or not user.is_active:
        revoke_auth_session(auth_session, now=now)
        db.commit()
        raise HTTPException(status_code=401, detail="User not found or inactive")

    if MFA_ENFORCEMENT_ENABLED and (
        not user.mfa_enabled or not auth_session.mfa_authenticated
    ):
        revoke_auth_session(auth_session, now=now)
        db.commit()
        response.delete_cookie("beacon_refresh", path="/users")
        raise HTTPException(status_code=401, detail="MFA authentication is required")

    rotated_token = rotate_refresh_token(auth_session, now=now)
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
        "session_expires_at": f"{(now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()}Z",
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
        revoke_auth_session(auth_session)
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
        AuthSession.refresh_expires_at > utc_now(),
    ).order_by(AuthSession.last_seen_at.desc()).all()
    return [serialize_auth_session(item, active_session_id) for item in sessions]


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
    revoke_auth_session(auth_session)
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
    now = utc_now()
    for item in sessions:
        revoke_auth_session(item, now=now)
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

    current_user.password_changed_at = utc_now()

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
    user = get_managed_user(db, current_user, user_id)

    old_role = assign_user_role(current_user, user, data.role)


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
    user = get_managed_user(db, current_user, user_id)

    set_user_active(current_user, user, False)

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
    user = get_managed_user(db, current_user, user_id)

    set_user_active(current_user, user, True)

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
