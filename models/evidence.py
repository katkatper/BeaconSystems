from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)

from database.connection import Base


class Evidence(Base):

    __tablename__ = "evidence"
    __table_args__ = (
        Index("ix_evidence_case_created", "case_id", "created_at"),
        Index(
            "uq_evidence_agency_content_sha256",
            "agency_id",
            "content_sha256",
            unique=True,
            postgresql_where=text("content_sha256 IS NOT NULL"),
            sqlite_where=text("content_sha256 IS NOT NULL"),
        ),
        Index(
            "ix_evidence_retention_disposition",
            "legal_hold",
            "disposition_status",
            "retention_until",
        ),
        CheckConstraint(
            "legal_hold = false OR legal_hold_reason IS NOT NULL",
            name="ck_evidence_legal_hold_reason",
        ),
    )


    evidence_id = Column(Integer, primary_key=True, index=True)

    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=False, index=True)


    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)


    description = Column(Text, nullable=True)
    evidence_type = Column(String(100), nullable=False)



    collected_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    evidence_location = Column(String(200), nullable=True)
    evidence_latitude = Column(Float, nullable=True)
    evidence_longitude = Column(Float, nullable=True)
    geocode_provider = Column(String(50), nullable=True)
    geocode_accuracy = Column(String(50), nullable=True)
    geocode_score = Column(Float, nullable=True)
    geocoded_address = Column(String(500), nullable=True)
    geocoded_at = Column(DateTime, nullable=True)
    custody_status = Column(String(100), default="collected")
    current_holder = Column(String(200), nullable=True)
    lab_reference = Column(String(200), nullable=True)
    available_at = Column(DateTime, nullable=True)

    is_sensitive = Column(Boolean, default=False)
    is_encrypted = Column(Boolean, default=False)
    encryption_key_id = Column(String(120), nullable=True)
    content_sha256 = Column(String(64), nullable=True)

    retention_policy_code = Column(String(100), nullable=False, default="agency-standard")
    retention_until = Column(DateTime, nullable=True)
    legal_hold = Column(Boolean, nullable=False, default=False)
    legal_hold_reason = Column(Text, nullable=True)
    legal_hold_set_at = Column(DateTime, nullable=True)
    legal_hold_set_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    disposition_status = Column(String(50), nullable=False, default="active")

    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=False, default=0, server_default="0")
    preview_path = Column(String(500), nullable=True)
    preview_sha256 = Column(String(64), nullable=True)
    preview_size_bytes = Column(BigInteger, nullable=False, default=0, server_default="0")
    storage_tier = Column(String(30), nullable=False, default="active", server_default="active")
    archived_at = Column(DateTime, nullable=True)



    collected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
