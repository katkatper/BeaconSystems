from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.connection import Base


class IntegrationSource(Base):
    __tablename__ = "integration_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(100), nullable=False)
    status = Column(String(50), default="pending")
    is_active = Column(Boolean, nullable=True)
    api_url = Column(String(500), nullable=True)

    # Provider-specific field names are mapped to Beacon's stable observation
    # contract. Credentials remain in the deployment secret manager and are
    # referenced at runtime; they are never stored in this table.
    adapter_key = Column(String(100), default="canonical_v1", nullable=False)
    field_mapping = Column(JSON, nullable=True)
    allowed_record_types = Column(JSON, nullable=True)
    match_threshold = Column(Integer, default=60, nullable=False)
    webhook_secret_hash = Column(String(255), nullable=True)
    rate_limit_per_minute = Column(Integer, nullable=False, default=120, server_default="120")
    consecutive_failures = Column(Integer, nullable=False, default=0, server_default="0")
    circuit_open_until = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    last_failure_reason = Column(Text, nullable=True)

    authorized_agencies = relationship(
        "IntegrationSourceAgency",
        back_populates="source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
