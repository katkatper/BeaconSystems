from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from database.connection import Base
from datetime import datetime


class CaseAccessGrant(Base):
    __tablename__ = "case_access_grants"

    grant_id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=True)

    reason = Column(Text, nullable=False)
    status = Column(String(50), default="active", nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
