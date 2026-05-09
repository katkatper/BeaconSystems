from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from database.connection import Base
from datetime import datetime


class Evidence(Base):

    __tablename__ = 'Evidence'

    evidence_id= Column(Integer, primary_key=True)

    case_id= Column(Integer)

    description= Column(Text)

    evidence_type= Column(String(100))

    collected_by= Column(Integer)

    evidence_location= Column(String(200))

    collected_at= Column(DateTime)

    created_at =Column(DateTime, default=datetime.utcnow)


