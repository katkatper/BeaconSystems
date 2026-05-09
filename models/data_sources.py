from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from database.connection import Base
from datetime import datetime

class Data_Source(Base):

    __tablename__ = 'Data_Sources'
    
    source_id= Column(Integer, primary_key=True)

    source_name= Column(String(100))

    source_type= Column(String(100))
    
    api_endpoint= Column(Text)

    contact_agency= Column(String(200))

    created_at = Column(DateTime, default=datetime.utcnow)