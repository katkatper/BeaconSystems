from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text

from database.connection import Base


class PartnerIntakeRecord(Base):
    __tablename__ = "partner_intake_records"

    intake_id = Column(Integer, primary_key=True, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=True, index=True)
    integration_source_id = Column(Integer, ForeignKey("integration_sources.id"), nullable=False)
    received_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    attached_external_record_id = Column(Integer, ForeignKey("external_records.id"), nullable=True)
    suggested_case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True)
    suggested_person_id = Column(Integer, ForeignKey("persons.person_id"), nullable=True)

    record_type = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=True)
    subject_name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geocode_provider = Column(String(50), nullable=True)
    geocode_accuracy = Column(String(50), nullable=True)
    geocode_score = Column(Float, nullable=True)
    geocoded_address = Column(String(500), nullable=True)
    geocoded_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=False)
    raw_data = Column(JSON, nullable=True)
    match_score = Column(Integer, nullable=True)
    match_reason = Column(Text, nullable=True)
    match_case_status = Column(String(50), nullable=True)
    intake_channel = Column(String(50), default="manual", nullable=False)
    legal_authority_type = Column(String(100), nullable=True)
    legal_authority_reference = Column(String(255), nullable=True)
    legal_authority_notes = Column(Text, nullable=True)

    status = Column(String(50), default="pending_review", nullable=False)
    review_notes = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
