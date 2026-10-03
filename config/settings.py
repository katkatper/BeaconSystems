import base64
import binascii
import os
from urllib.parse import urlsplit

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_csv(name: str) -> list[str]:
    return [
        value.strip()
        for value in os.getenv(name, "").split(",")
        if value.strip()
    ]


ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
IS_PRODUCTION = ENVIRONMENT in {"production", "prod"}
CORS_ORIGINS = env_csv("CORS_ORIGINS")
TRUSTED_HOSTS = env_csv("TRUSTED_HOSTS")
HSTS_MAX_AGE_SECONDS = int(os.getenv("HSTS_MAX_AGE_SECONDS", "31536000"))
ENABLE_LOCAL_SCHEMA_BOOTSTRAP = env_bool(
    "ENABLE_LOCAL_SCHEMA_BOOTSTRAP",
    default=ENVIRONMENT in {"development", "dev", "test"},
)
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
DATABASE_POOL_RECYCLE_SECONDS = int(
    os.getenv("DATABASE_POOL_RECYCLE_SECONDS", "1800")
)
DATABASE_SLOW_QUERY_MS = float(os.getenv("DATABASE_SLOW_QUERY_MS", "500"))
API_REQUEST_TIMEOUT_SECONDS = float(os.getenv("API_REQUEST_TIMEOUT_SECONDS", "30"))
AWS_CONNECT_TIMEOUT_SECONDS = float(os.getenv("AWS_CONNECT_TIMEOUT_SECONDS", "5"))
AWS_READ_TIMEOUT_SECONDS = float(os.getenv("AWS_READ_TIMEOUT_SECONDS", "10"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
OBJECT_STORAGE_BACKEND = os.getenv("OBJECT_STORAGE_BACKEND", "local").strip().lower()
OBJECT_STORAGE_BUCKET = os.getenv("OBJECT_STORAGE_BUCKET", "").strip()
OBJECT_STORAGE_PREFIX = os.getenv("OBJECT_STORAGE_PREFIX", "beacon").strip().strip("/")
OBJECT_STORAGE_LOCAL_ROOT = os.getenv("OBJECT_STORAGE_LOCAL_ROOT", "uploads").strip()
OBJECT_STORAGE_KMS_KEY_ID = os.getenv("OBJECT_STORAGE_KMS_KEY_ID", "").strip()
OBJECT_STORAGE_EXPECTED_OWNER = os.getenv("OBJECT_STORAGE_EXPECTED_OWNER", "").strip()
OBJECT_STORAGE_SIGNED_URL_TTL_SECONDS = int(
    os.getenv("OBJECT_STORAGE_SIGNED_URL_TTL_SECONDS", "300")
)
RATE_LIMIT_REDIS_URL = os.getenv("RATE_LIMIT_REDIS_URL", "").strip()
RATE_LIMIT_REDIS_TIMEOUT_SECONDS = float(
    os.getenv("RATE_LIMIT_REDIS_TIMEOUT_SECONDS", "5")
)
LOGIN_RATE_LIMIT_ATTEMPTS = int(os.getenv("LOGIN_RATE_LIMIT_ATTEMPTS", "10"))
LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "300")
)
MFA_RATE_LIMIT_ATTEMPTS = int(os.getenv("MFA_RATE_LIMIT_ATTEMPTS", "10"))
MFA_RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("MFA_RATE_LIMIT_WINDOW_SECONDS", "300")
)
REFRESH_RATE_LIMIT_ATTEMPTS = int(os.getenv("REFRESH_RATE_LIMIT_ATTEMPTS", "60"))
REFRESH_RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("REFRESH_RATE_LIMIT_WINDOW_SECONDS", "60")
)

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
MFA_SECRET_ENCRYPTION_KEY = os.getenv("MFA_SECRET_ENCRYPTION_KEY", "").strip()
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
JWT_ISSUER = os.getenv("JWT_ISSUER", "beacon-api").strip()
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "beacon-web").strip()
PARTNER_WEBHOOK_TOKEN = os.getenv("PARTNER_WEBHOOK_TOKEN")
EVIDENCE_ENCRYPTION_ENABLED = os.getenv("EVIDENCE_ENCRYPTION_ENABLED", "false").lower() == "true"
EVIDENCE_ENCRYPTION_KEY_ID = os.getenv("EVIDENCE_ENCRYPTION_KEY_ID", "local-storage")
SPLUNK_HEC_URL = os.getenv("SPLUNK_HEC_URL")
SPLUNK_HEC_TOKEN = os.getenv("SPLUNK_HEC_TOKEN")
ARCGIS_GEOCODING_ENABLED = os.getenv("ARCGIS_GEOCODING_ENABLED", "false").lower() == "true"
ARCGIS_API_KEY = os.getenv("ARCGIS_API_KEY")
ARCGIS_GEOCODE_URL = os.getenv(
    "ARCGIS_GEOCODE_URL",
    "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates",
)
ARCGIS_GEOCODE_FOR_STORAGE = os.getenv("ARCGIS_GEOCODE_FOR_STORAGE", "true").lower() == "true"
ARCGIS_GEOCODE_TIMEOUT_SECONDS = float(os.getenv("ARCGIS_GEOCODE_TIMEOUT_SECONDS", "5"))
ARCGIS_GEOCODE_MIN_SCORE = float(os.getenv("ARCGIS_GEOCODE_MIN_SCORE", "80"))


def validate_runtime_settings() -> None:
    if not IS_PRODUCTION:
        return

    errors = []

    if not SECRET_KEY or len(SECRET_KEY) < 32:
        errors.append("SECRET_KEY must contain at least 32 characters")

    if not MFA_SECRET_ENCRYPTION_KEY:
        errors.append("MFA_SECRET_ENCRYPTION_KEY is required in production")
    else:
        try:
            decoded_mfa_key = base64.urlsafe_b64decode(
                MFA_SECRET_ENCRYPTION_KEY.encode("ascii")
            )
            if len(decoded_mfa_key) != 32:
                raise ValueError
        except (ValueError, UnicodeEncodeError, binascii.Error):
            errors.append("MFA_SECRET_ENCRYPTION_KEY must be a valid Fernet key")

    if not JWT_ISSUER:
        errors.append("JWT_ISSUER is required in production")

    if not JWT_AUDIENCE:
        errors.append("JWT_AUDIENCE is required in production")

    if ACCESS_TOKEN_EXPIRE_MINUTES <= 0 or REFRESH_TOKEN_EXPIRE_DAYS <= 0:
        errors.append("Token expiration settings must be greater than zero")

    if not CORS_ORIGINS:
        errors.append("CORS_ORIGINS must list approved production frontend origins")

    if "*" in CORS_ORIGINS:
        errors.append("CORS_ORIGINS cannot contain '*' in production")

    for origin in CORS_ORIGINS:
        parsed_origin = urlsplit(origin)
        if (
            parsed_origin.scheme != "https"
            or not parsed_origin.netloc
            or parsed_origin.path not in {"", "/"}
            or parsed_origin.query
            or parsed_origin.fragment
        ):
            errors.append(
                "CORS_ORIGINS entries must be HTTPS origins without paths in production"
            )
            break

    if not TRUSTED_HOSTS:
        errors.append("TRUSTED_HOSTS must list approved production hostnames")

    if "*" in TRUSTED_HOSTS:
        errors.append("TRUSTED_HOSTS cannot contain '*' in production")

    if HSTS_MAX_AGE_SECONDS < 31536000:
        errors.append("HSTS_MAX_AGE_SECONDS must be at least 31536000 in production")

    if ENABLE_LOCAL_SCHEMA_BOOTSTRAP:
        errors.append("ENABLE_LOCAL_SCHEMA_BOOTSTRAP must be false in production")

    if OBJECT_STORAGE_BACKEND != "s3":
        errors.append("OBJECT_STORAGE_BACKEND must be 's3' in production")

    if not OBJECT_STORAGE_BUCKET:
        errors.append("OBJECT_STORAGE_BUCKET is required in production")

    if not OBJECT_STORAGE_KMS_KEY_ID:
        errors.append("OBJECT_STORAGE_KMS_KEY_ID is required in production")

    if (
        not OBJECT_STORAGE_EXPECTED_OWNER
        or len(OBJECT_STORAGE_EXPECTED_OWNER) != 12
        or not OBJECT_STORAGE_EXPECTED_OWNER.isdigit()
    ):
        errors.append(
            "OBJECT_STORAGE_EXPECTED_OWNER must be a 12 digit AWS account ID in production"
        )

    if API_REQUEST_TIMEOUT_SECONDS <= 0:
        errors.append("API_REQUEST_TIMEOUT_SECONDS must be greater than zero")

    if AWS_CONNECT_TIMEOUT_SECONDS <= 0 or AWS_READ_TIMEOUT_SECONDS <= 0:
        errors.append("AWS connection and read timeouts must be greater than zero")

    if MAX_UPLOAD_BYTES <= 0:
        errors.append("MAX_UPLOAD_BYTES must be greater than zero")

    if not RATE_LIMIT_REDIS_URL:
        errors.append("RATE_LIMIT_REDIS_URL is required in production")
    elif not RATE_LIMIT_REDIS_URL.lower().startswith("rediss://"):
        errors.append("RATE_LIMIT_REDIS_URL must use TLS (rediss://) in production")

    if RATE_LIMIT_REDIS_TIMEOUT_SECONDS <= 0:
        errors.append("RATE_LIMIT_REDIS_TIMEOUT_SECONDS must be greater than zero")

    rate_limit_values = {
        "LOGIN_RATE_LIMIT_ATTEMPTS": LOGIN_RATE_LIMIT_ATTEMPTS,
        "LOGIN_RATE_LIMIT_WINDOW_SECONDS": LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        "MFA_RATE_LIMIT_ATTEMPTS": MFA_RATE_LIMIT_ATTEMPTS,
        "MFA_RATE_LIMIT_WINDOW_SECONDS": MFA_RATE_LIMIT_WINDOW_SECONDS,
        "REFRESH_RATE_LIMIT_ATTEMPTS": REFRESH_RATE_LIMIT_ATTEMPTS,
        "REFRESH_RATE_LIMIT_WINDOW_SECONDS": REFRESH_RATE_LIMIT_WINDOW_SECONDS,
    }
    for name, value in rate_limit_values.items():
        if value <= 0:
            errors.append(f"{name} must be greater than zero")

    if errors:
        raise RuntimeError("Invalid production configuration: " + "; ".join(errors))

