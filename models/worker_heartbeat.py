from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from database.connection import Base


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"

    worker_id = Column(String(200), primary_key=True)
    status = Column(String(30), nullable=False, default="idle")
    current_job_id = Column(Integer, ForeignKey("async_jobs.job_id"), nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
