from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.connection import Base


class IntegrationSourceAgency(Base):
    __tablename__ = "integration_source_agencies"
    __table_args__ = (
        UniqueConstraint(
            "integration_source_id",
            "agency_id",
            name="uq_integration_source_agency",
        ),
        Index("ix_integration_source_agencies_source", "integration_source_id"),
        Index("ix_integration_source_agencies_agency", "agency_id"),
    )

    id = Column(Integer, primary_key=True)
    integration_source_id = Column(
        Integer,
        ForeignKey("integration_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    agency_id = Column(
        Integer,
        ForeignKey("agencies.agency_id", ondelete="CASCADE"),
        nullable=False,
    )
    jurisdiction = Column(String(255), nullable=True)
    allowed_record_types = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source = relationship("IntegrationSource", back_populates="authorized_agencies")
