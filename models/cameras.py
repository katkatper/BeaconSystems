from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from database.connection import Base
from datetime import datetime



class Cameras(Base):

    __tablename__ = 'Cameras'

    camera_id = Column(Integer, primary_key=True)

    name = Column (String(100))

    location = Column (Text)

    longitude = Column(Float)

    latitude= Column(Float)

    owner_agency_id= Column(Integer) 

    camera_type= Column(String(100))

    created_at =Column(DateTime, default=datetime.utcnow)


