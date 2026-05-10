from turtle import title
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from database.connection import Base
from datetime import datetime

class Alerts(Base):

    __tablename__ = 'alerts'

    alert_id = Column(Integer, primary_key=True, index=True)


    case_id=Column(Integer, ForeignKey('cases.case_id'))


    person_id= Column(Integer, ForeignKey('persons.person_id'))


    recipient_agency_id= Column(Integer)


    alert_type= Column(String(100))


    severity= Column(String(50), default="medium")


    title= Column(String(255))


    description= Column(Text)


    alert_status= Column(String(50)) 


    created_at = Column(DateTime, default=datetime.utcnow)


