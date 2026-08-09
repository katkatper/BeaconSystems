from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database.connection import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)

    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=True, index=True)


    person_id = Column(Integer, ForeignKey("persons.person_id"))

    external_record_id = Column(Integer, ForeignKey("external_records.id"))


    score = Column(Integer, nullable=False)

    status = Column(String, default="pending_review")


    created_at = Column(DateTime(timezone=True), server_default=func.now())
