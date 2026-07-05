from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from database.connection import Base


#EXTERNAL INTELLIGENCE DIGESTION

class ExternalRecord(Base):

    __tablename__ = "external_records"

    id = Column(Integer, primary_key=True, index=True)


    integration_source_id = Column(Integer, ForeignKey("integration_sources.id"))

    person_id= Column(Integer, ForeignKey("persons.person_id"), nullable=True)

    case_id= Column(Integer, ForeignKey("cases.case_id"), nullable=True)


    record_type = Column(String, nullable=False)

    external_id = Column(String, nullable=True)


    first_name = Column(String, nullable=True)

    last_name = Column(String, nullable=True)

    age = Column(Integer, nullable=True)


    location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geocode_provider = Column(String(50), nullable=True)
    geocode_accuracy = Column(String(50), nullable=True)
    geocode_score = Column(Float, nullable=True)
    geocoded_address = Column(String(500), nullable=True)
    geocoded_at = Column(DateTime, nullable=True)

    notes = Column(String, nullable=True)

    raw_data = Column(JSON, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now())




