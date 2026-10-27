import hashlib
import hmac

from config.settings import SECRET_KEY

TOKEN_HASH_PREFIX = "hmac-sha256$"


def hash_partner_token(token: str) -> str:
    digest = hmac.new(
        SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{TOKEN_HASH_PREFIX}{digest}"


def verify_partner_token(token: str, stored_hash: str) -> bool:
    if not stored_hash.startswith(TOKEN_HASH_PREFIX):
        return False
    return hmac.compare_digest(hash_partner_token(token), stored_hash)


def is_partner_token_hash(stored_hash: str) -> bool:
    return stored_hash.startswith(TOKEN_HASH_PREFIX)
