from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from database.connection import Base
from datetime import datetime
from sqlalchemy.orm import relationship


class Cases(Base):

    __tablename__ = "cases"

    case_id = Column(Integer, primary_key=True, index=True)


    case_number = Column(String(100), unique=True, nullable=False)

    title = Column(String(255), nullable=False)

    date_opened = Column(DateTime)


    person_id = Column(Integer, ForeignKey("persons.person_id"), nullable=False)

    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=False)


    description = Column(Text, nullable=True)

    investigator_id = Column(Integer)

    last_seen_location = Column(String(100))

    priority_level = Column(String(50), default="medium")

    notes = Column(Text)

    case_status = Column(String(50), default="Open")


    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    person = relationship("Person", back_populates="cases")