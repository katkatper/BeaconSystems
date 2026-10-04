import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote


MFA_ISSUER = "Beacon"
MFA_STEP_SECONDS = 30
MFA_DIGITS = 6


def generate_mfa_secret() -> str:
    """Generate a 160-bit Base32 secret suitable for TOTP enrollment."""
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8").rstrip("=")


def _normalized_secret(secret: str) -> str:
    return secret + ("=" * (-len(secret) % 8))


def generate_totp(secret: str, for_time: float | None = None) -> str:
    """Generate Beacon's six-digit, SHA-1 TOTP value for a point in time."""
    key = base64.b32decode(_normalized_secret(secret), casefold=True)
    counter = int((time.time() if for_time is None else for_time) // MFA_STEP_SECONDS)
    message = struct.pack(">Q", counter)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10**MFA_DIGITS)).zfill(MFA_DIGITS)


def verify_totp(secret: str | None, code: str, at_time: float | None = None) -> bool:
    """Verify a TOTP code with one 30-second window of clock tolerance."""
    if not secret:
        return False

    clean_code = "".join(character for character in code if character.isdigit())
    if len(clean_code) != MFA_DIGITS:
        return False

    now = time.time() if at_time is None else at_time
    return any(
        hmac.compare_digest(
            generate_totp(secret, now + (window * MFA_STEP_SECONDS)),
            clean_code,
        )
        for window in range(-1, 2)
    )


def build_otpauth_uri(username: str, secret: str) -> str:
    """Build the standards-compatible enrollment URI shown to authenticator apps."""
    account = quote(f"{MFA_ISSUER}:{username}")
    issuer = quote(MFA_ISSUER)
    return (
        f"otpauth://totp/{account}?secret={secret}&issuer={issuer}"
        f"&digits={MFA_DIGITS}&period={MFA_STEP_SECONDS}"
    )
