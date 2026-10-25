from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from sqlalchemy.sql import func
from database.connection import Base


class IntegrationSource(Base):

    __tablename__ = "integration_sources"

    id = Column(Integer, primary_key=True, index=True)


    name = Column(String(255), nullable=False)

    source_type= Column(String(100), nullable=False)



    status= Column(String(50), default="pending")

    is_active= Column(Boolean, nullable=True)



    api_url= Column(String(500), nullable=True)

    # Provider-specific field names are mapped to Beacon's stable observation
    # contract. Credentials remain in the deployment secret manager and are
    # referenced at runtime; they are never stored in this table.
    adapter_key = Column(String(100), default="canonical_v1", nullable=False)
    field_mapping = Column(JSON, nullable=True)
    allowed_record_types = Column(JSON, nullable=True)
    authorized_agency_ids = Column(JSON, nullable=True)
    match_threshold = Column(Integer, default=60, nullable=False)
    webhook_secret_hash = Column(String(255), nullable=True)

    description = Column(String(500), nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now())




