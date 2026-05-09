from sqlalchemy import Column, Integer, String, DateTime, Text
from database.connection import Base
from datetime import datetime


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)

    action = Column(String(100), nullable=False)

    entity = Column(String(100), nullable=False)

    entity_id = Column(Integer, nullable=True)

    details = Column(Text, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)





