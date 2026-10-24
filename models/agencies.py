from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, Text

from database.connection import Base


class Agencies(Base):

    __tablename__ = 'agencies'
    __table_args__ = (
        CheckConstraint(
            "lifecycle_status IN ('active', 'suspended', 'offboarded')",
            name="ck_agencies_lifecycle_status",
        ),
    )
    
    agency_id=Column(Integer, primary_key=True)

    agency_name= Column(String(200))

    agency_type= Column(String(100))

    city= Column(String(100))

    state= Column(String(100))

    country= Column(String(100))

    contact_phone= Column(String(50))

    contact_email= Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    lifecycle_status = Column(String(20), nullable=False, default="active")
    status_changed_at = Column(DateTime, nullable=True)
    status_reason = Column(Text, nullable=True)

