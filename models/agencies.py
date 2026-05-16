from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from database.connection import Base
from datetime import datetime

class Agencies(Base):

    __tablename__ = 'agencies'
    
    agency_id=Column(Integer, primary_key=True)

    agency_name= Column(String(200))

    agency_type= Column(String(100))

    city= Column(String(100))

    state= Column(String(100))

    country= Column(String(100))

    contact_phone= Column(String(50))

    contact_email= Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)



