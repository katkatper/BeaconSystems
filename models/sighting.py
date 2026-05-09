from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from database.connection import Base
from datetime import datetime

class Sighting(Base):  

    __tablename__= "sightings"  #table name in the database

 

    sighting_id= Column(Integer, primary_key=True, index=True) # Primary key 

    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False) #foreign key to link to cases table

    person_id= Column(Integer)

    location= Column(Text)

    longitude= Column(Float)

    latitude= Column(Float)

    sighting_time= Column(DateTime)

    description= Column(Text)   

    confidence_score= Column(Float)

    image_url= Column(Text)

    created_at= Column(DateTime, default=datetime.utcnow)   


