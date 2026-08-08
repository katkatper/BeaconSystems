import os

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
ENABLE_LOCAL_SCHEMA_BOOTSTRAP = env_bool(
    "ENABLE_LOCAL_SCHEMA_BOOTSTRAP",
    default=ENVIRONMENT in {"development", "dev", "test"},
)
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
DATABASE_POOL_RECYCLE_SECONDS = int(
    os.getenv("DATABASE_POOL_RECYCLE_SECONDS", "1800")
)

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
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

    if not CORS_ORIGINS:
        errors.append("CORS_ORIGINS must list approved production frontend origins")

    if "*" in CORS_ORIGINS:
        errors.append("CORS_ORIGINS cannot contain '*' in production")

    if ENABLE_LOCAL_SCHEMA_BOOTSTRAP:
        errors.append("ENABLE_LOCAL_SCHEMA_BOOTSTRAP must be false in production")

    if errors:
        raise RuntimeError("Invalid production configuration: " + "; ".join(errors))

