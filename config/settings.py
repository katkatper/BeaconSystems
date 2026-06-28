import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

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

