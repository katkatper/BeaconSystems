from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from database.connection import Base
from datetime import datetime


class ActivityLog(Base):

    __tablename__ = "activity_log"
    __table_args__ = (
        Index("ix_activity_log_agency_created", "agency_id", "timestamp"),
    )


    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=True)
    agency_id = Column(Integer, nullable=True)


    action = Column(String(100), nullable=False)


    entity = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)

    details = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)





