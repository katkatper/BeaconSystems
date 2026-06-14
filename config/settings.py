import os
from dotenv import load_dotenv

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

