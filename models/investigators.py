from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from database.connection import Base
from datetime import datetime

class Investigators(Base):

    __tablename__ = 'Investigators'

    investigator_id= Column(Integer, primary_key=True)
    
    agency_id= Column(Integer)

    first_name= Column(String(100))
    
    last_name= Column(String(100))

    badge_number= Column(String(50))

    role= Column(String(100))

    phone= Column(String(50))

    email= Column(String(100))

    access_level= Column(String(20))

    created_at = Column(DateTime, default=datetime.utcnow)
