from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, Integer, String, Text

from database.connection import Base


class Agencies(Base):

    __tablename__ = 'agencies'
    __table_args__ = (
        CheckConstraint(
            "lifecycle_status IN ('active', 'suspended', 'offboarded')",
            name="ck_agencies_lifecycle_status",
        ),
        CheckConstraint(
            "storage_quota_bytes IS NULL OR storage_quota_bytes > 0",
            name="ck_agencies_storage_quota_positive",
        ),
        CheckConstraint(
            "monthly_provider_request_quota IS NULL OR monthly_provider_request_quota > 0",
            name="ck_agencies_provider_quota_positive",
        ),
        CheckConstraint(
            "monthly_job_quota IS NULL OR monthly_job_quota > 0",
            name="ck_agencies_job_quota_positive",
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
    storage_quota_bytes = Column(BigInteger, nullable=True)
    monthly_provider_request_quota = Column(Integer, nullable=True)
    monthly_job_quota = Column(Integer, nullable=True)

