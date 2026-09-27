import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from config.settings import IS_PRODUCTION, MFA_SECRET_ENCRYPTION_KEY, SECRET_KEY


ENCRYPTED_PREFIX = "enc:v1:"


def _fernet() -> Fernet:
    configured_key = MFA_SECRET_ENCRYPTION_KEY
    if not configured_key:
        if IS_PRODUCTION:
            raise RuntimeError("MFA secret encryption is not configured")
        configured_key = base64.urlsafe_b64encode(
            hashlib.sha256(SECRET_KEY.encode("utf-8")).digest()
        ).decode("ascii")
    try:
        return Fernet(configured_key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise RuntimeError("MFA_SECRET_ENCRYPTION_KEY is invalid") from exc


def encrypt_mfa_secret(secret: str) -> str:
    token = _fernet().encrypt(secret.encode("utf-8")).decode("ascii")
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_mfa_secret(stored_secret: str) -> tuple[str, bool]:
    """Return the clear secret and whether a legacy plaintext value was read."""
    if not stored_secret.startswith(ENCRYPTED_PREFIX):
        return stored_secret, True
    token = stored_secret[len(ENCRYPTED_PREFIX):]
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8"), False
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise RuntimeError("Stored MFA secret could not be decrypted") from exc
