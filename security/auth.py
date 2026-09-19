from datetime import datetime, timedelta, timezone
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
    SECRET_KEY,
)
from database.connection import get_db
from database.tenant_context import configure_tenant_session
from models.user import User
from models.auth_session import AuthSession


if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in the environment")


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/login",
)


# -------------------------------------------------------------------
# Password utilities
# -------------------------------------------------------------------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# -------------------------------------------------------------------
# JWT utilities
# -------------------------------------------------------------------

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
    token_type: str = "access",
) -> str:
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "jti": str(uuid.uuid4()),
        "token_type": token_type,
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
        audience=JWT_AUDIENCE,
        issuer=JWT_ISSUER,
    )
    if payload.get("token_type") != "access":
        raise JWTError("Invalid token type")
    return payload


# -------------------------------------------------------------------
# Current authenticated user
# -------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)

        user_id = int(payload.get("sub"))
        auth_version = int(payload.get("auth_version"))
        session_id = str(payload.get("sid") or "")

        if user_id <= 0 or auth_version < 0 or not session_id:
            raise credentials_exception

    except (JWTError, TypeError, ValueError):
        raise credentials_exception

    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if (
        user is None
        or not user.is_active
        or user.auth_version != auth_version
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_session = db.query(AuthSession).filter(
        AuthSession.session_id == session_id,
        AuthSession.user_id == user.user_id,
        AuthSession.revoked_at.is_(None),
        AuthSession.expires_at > datetime.utcnow(),
    ).first()
    if auth_session is None:
        raise credentials_exception

    configure_tenant_session(
        db,
        agency_id=user.agency_id,
        platform_admin=user.role == "platform_admin",
    )

    return user


# -------------------------------------------------------------------
# Role-based access control
# -------------------------------------------------------------------

def require_role(*allowed_roles: str):
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive account",
            )

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized",
            )

        return current_user

    return role_checker
