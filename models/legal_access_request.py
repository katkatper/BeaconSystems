from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from database.connection import Base
from datetime import datetime


class LegalAccessRequest(Base):
    __tablename__ = "legal_access_requests"

    request_id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True)
    person_id = Column(Integer, ForeignKey("persons.person_id"), nullable=True)
    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=True)
    requested_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    assigned_investigator_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    requester_name = Column(String(255), nullable=False)
    requester_organization = Column(String(255), nullable=False)
    requester_role = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=True)

    authority_type = Column(String(100), nullable=False)
    request_type = Column(String(100), nullable=True)
    source_type = Column(String(100), nullable=False)
    receiving_entity = Column(String(255), nullable=True)
    target_identifier = Column(String(255), nullable=True)
    jurisdiction = Column(String(255), nullable=True)
    legal_reference = Column(String(255), nullable=True)

    purpose = Column(Text, nullable=False)
    reason_for_request = Column(Text, nullable=True)
    scope_description = Column(Text, nullable=False)
    probable_cause_summary = Column(Text, nullable=True)
    minimization_plan = Column(Text, nullable=True)
    retention_plan = Column(Text, nullable=True)
    document_location = Column(String(500), nullable=True)
    attachments = Column(Text, nullable=True)

    status = Column(String(50), default="pending", nullable=False)
    priority = Column(String(50), default="routine", nullable=False)
    review_notes = Column(Text, nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
