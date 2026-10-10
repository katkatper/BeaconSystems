
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, Text, Float
from database.connection import Base
from datetime import datetime

class Alerts(Base):

    __tablename__ = 'alerts'
    __table_args__ = (
        Index("ix_alerts_case_created", "case_id", "created_at"),
        Index("ix_alerts_recipient_created", "recipient_agency_id", "created_at"),
    )

    alert_id = Column(Integer, primary_key=True, index=True)


    case_id=Column(Integer, ForeignKey('cases.case_id'))


    person_id= Column(Integer, ForeignKey('persons.person_id'))


    recipient_agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=False)

    alert_type= Column(String(100))

    alert_source = Column(String(100), nullable=True)


    source_detail = Column(String(255), nullable=True)


    confidence_score = Column(Float, nullable=True)


    severity= Column(String(50), default="medium")


    title= Column(String(255))


    description= Column(Text)


    alert_status= Column(String(50)) 


    created_at = Column(DateTime, default=datetime.utcnow)


