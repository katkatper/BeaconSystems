from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from database.connection import Base
from datetime import datetime


class User(Base):

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)


    username = Column(String, unique=True, nullable=False)

    email = Column(String, unique=True, nullable=False)

    password_hash = Column(String, nullable=False)


    role = Column(String, default="viewer")  # ADMIN, INVESTIGATOR, ANALYST, VIEWER

    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=True)


    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)