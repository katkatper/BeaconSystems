import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


load_dotenv()


def build_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return database_url

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_name = os.getenv("DB_NAME")
    db_port = os.getenv("DB_PORT", "5432")

    if db_user and db_password and db_host and db_name:
        return (
            f"postgresql+psycopg2://{db_user}:{quote_plus(db_password)}"
            f"@{db_host}:{db_port}/{db_name}"
        )

    raise RuntimeError(
        "Set DATABASE_URL or DB_USER/DB_PASSWORD/DB_HOST/DB_NAME before starting Beacon."
    )


DATABASE_URL = build_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
