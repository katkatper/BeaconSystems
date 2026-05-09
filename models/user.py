from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from database.connection import Base
from datetime import datetime

class User(Base):

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, nullable=False)

    email = Column(String, unique=True, nullable=False)

    password_hash = Column(String, nullable=False)

    role= Column(String, default="user")    #ADMIN, INVESTIGATOR, ANALYST, VIEWER

    is_active= Column (Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)