from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from database.connection import Base


class AgencyExchange(Base):
    __tablename__ = "agency_exchanges"

    exchange_id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    from_agency = Column(String(200), nullable=False)
    to_agency = Column(String(200), nullable=False)
    requesting_officer = Column(String(200), nullable=True)
    badge_number = Column(String(80), nullable=True)
    subject = Column(String(255), nullable=True)
    request_type = Column(String(120), nullable=True)
    information_type = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    legal_authority = Column(String(200), nullable=True)
    priority = Column(String(50), default="routine")
    due_date = Column(DateTime, nullable=True)
    delivery_method = Column(String(100), nullable=True)
    requested_records = Column(Text, nullable=True)
    attachments = Column(Text, nullable=True)
    assigned_to = Column(String(200), nullable=True)
    requested_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    audit_log = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    fulfilled_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="submitted")
    created_at = Column(DateTime, default=datetime.utcnow)
