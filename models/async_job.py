from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint

from database.connection import Base


class AsyncJob(Base):
    __tablename__ = "async_jobs"
    __table_args__ = (
        UniqueConstraint("agency_id", "idempotency_key", name="uq_async_jobs_agency_idempotency"),
        Index("ix_async_jobs_claim", "status", "available_at", "priority", "created_at"),
        Index("ix_async_jobs_agency_created", "agency_id", "created_at"),
    )

    job_id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=False)
    job_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    idempotency_key = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False, default="queued")
    priority = Column(Integer, nullable=False, default=0)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    replay_count = Column(Integer, nullable=False, default=0)
    available_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    locked_at = Column(DateTime, nullable=True)
    locked_by = Column(String(200), nullable=True)
    last_error = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
