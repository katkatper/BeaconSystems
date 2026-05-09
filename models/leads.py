from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from database.connection import Base
from datetime import datetime

class Leads(Base):

    __tablename__ = 'Leads'

    lead_id = Column(Integer, primary_key=True)

    case_id = Column(Integer)

    lead_source= Column(String(100))

    description= Column(Text)

    confidence_score= Column(Float)

    status= Column (String(50)) 

    created_at = Column(DateTime, default=datetime.utcnow)

