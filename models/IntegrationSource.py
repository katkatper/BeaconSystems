from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from database.connection import Base\


class IntegrationSource(Base):

    __tablename__ = "integration_sources"

    id = Column(Integer, primary_key=True, index=True)


    name = Column(String(255), nullable=False)

    source_type= Column(String(100), nullable=False)



    status= Column(String(50), default="pending")

    is_active= Column(Boolean, nullable=True)



    api_url= Column(String(500), nullable=True)

    description = Column(String(500), nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now())




