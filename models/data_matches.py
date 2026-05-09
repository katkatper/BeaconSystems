from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from database.connection import Base
from datetime import datetime



class Data_Matches(Base):

    __tablename__ = 'Data Matches'

    match_id = Column(Integer, primary_key=True)

    case_id = Column(Integer)

    data_source_id = Column(Integer)

    match_type= Column(String(100))

    match_details= Column(Text) 

    confidence_score = Column(Float)

    matched_at = Column(DateTime, default=datetime.utcnow)


