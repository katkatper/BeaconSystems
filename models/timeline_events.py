from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from database.connection import Base


class Timeline_Event(Base):

    __tablename__ = 'Timeline_events'


    event_id = Column(Integer, primary_key=True, index=True) 


    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)


    person_id = Column(Integer, ForeignKey("persons.person_id"), nullable=True)


    event_type = Column(String(100), nullable=False)


    source_type = Column(String(100), nullable=True)


    location = Column(String(255), nullable=True)


    description = Column(Text, nullable=True)


    timestamp = Column(DateTime, default=datetime.utcnow)


    created_at = Column(DateTime, default=datetime.utcnow)