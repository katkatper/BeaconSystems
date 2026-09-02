import os
import psycopg2

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", "5432"),
    sslmode=os.getenv("DB_SSLMODE", "verify-full"),
    sslrootcert=os.getenv("DB_SSLROOTCERT", "global-bundle.pem"),
)
