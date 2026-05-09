from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import SessionLocal


router=APIRouter()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
            db.close()
# routes/users_routes.py

router = APIRouter()

@router.get("/")
def alerts_routes():
    return {"message": "All Alerts"}

@router.post("/")
def create_alerts(Alerts: dict):

    # replace with database logic
    return {"message": "Alerts created", "data": Alerts}