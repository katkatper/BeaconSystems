from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from database.connection import Base
from datetime import datetime


class LegalAccessRequest(Base):
    __tablename__ = "legal_access_requests"

    request_id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True)
    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=True)
    requested_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    requester_name = Column(String(255), nullable=False)
    requester_organization = Column(String(255), nullable=False)
    requester_role = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=True)

    authority_type = Column(String(100), nullable=False)
    source_type = Column(String(100), nullable=False)
    target_identifier = Column(String(255), nullable=True)
    jurisdiction = Column(String(255), nullable=True)
    legal_reference = Column(String(255), nullable=True)

    purpose = Column(Text, nullable=False)
    scope_description = Column(Text, nullable=False)
    minimization_plan = Column(Text, nullable=True)
    retention_plan = Column(Text, nullable=True)
    document_location = Column(String(500), nullable=True)

    status = Column(String(50), default="pending", nullable=False)
    review_notes = Column(Text, nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
