from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from database.connection import Base


class AgencyExchange(Base):
    __tablename__ = "agency_exchanges"

    exchange_id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    from_agency = Column(String(200), nullable=False)
    to_agency = Column(String(200), nullable=False)
    information_type = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    legal_authority = Column(String(200), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    status = Column(String(50), default="approved")
    created_at = Column(DateTime, default=datetime.utcnow)
