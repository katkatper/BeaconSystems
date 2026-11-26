"""Create a Beacon platform admin for a local development database only."""

from getpass import getpass

from sqlalchemy import func

from config.settings import ENVIRONMENT
from database.connection import SessionLocal, engine
from models.agencies import Agencies
from models.user import User
from schemas.user_schema import UserCreate
from security.auth import hash_password
from services.clock import utc_now


def main():
    if ENVIRONMENT not in {"development", "dev"} or engine.url.host not in {"127.0.0.1", "::1"}:
        raise SystemExit("Refusing to run outside local Beacon development.")
    if any(key in engine.url.query for key in ("host", "hostaddr", "service", "servicefile")):
        raise SystemExit("Refusing a database URL with connection overrides.")

    with SessionLocal() as db:
        agencies = db.query(Agencies).filter_by(lifecycle_status="active").order_by(Agencies.agency_id).all()
        if not agencies:
            raise SystemExit("Create an active local test agency first.")
        for agency in agencies:
            print(f"{agency.agency_id}: {agency.agency_name}")
        choice = input("Local test agency ID: ").strip()
        if choice not in {str(agency.agency_id) for agency in agencies}:
            raise SystemExit("Select an active agency from the list.")
        username = input("New admin username: ").strip()
        email = input("New admin email: ").strip().lower()
        password = getpass("New admin password: ")
        if password != getpass("Repeat password: "):
            raise SystemExit("Passwords did not match.")
        if not username or len(password) < 12 or len(password.encode("utf-8")) > 72:
            raise SystemExit("Enter a username and a password of at least 12 characters and at most 72 bytes.")
        try:
            data = UserCreate(username=username, email=email, password=password)
        except ValueError:
            raise SystemExit("Enter a valid email address.") from None
        if db.query(User.user_id).filter(
            (func.lower(User.username) == username.lower()) | (func.lower(User.email) == email)
        ).first():
            raise SystemExit("That username or email already exists. No account was changed.")
        db.add(User(
            username=data.username, email=data.email, password_hash=hash_password(data.password),
            agency_id=int(choice), role="platform_admin", is_active=True, password_changed_at=utc_now(),
        ))
        db.commit()
        print("Local platform admin created. Sign in to Beacon to continue.")


if __name__ == "__main__":
    main()
