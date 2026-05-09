from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from database.connection import Base
from datetime import datetime

class Alerts(Base):

    __tablename__ = 'Alerts'

    alert_id = Column(Integer, primary_key=True)

    case_id=Column(Integer)

    recipient_agency_id= Column(Integer)

    alert_type= Column(String)

    alert_status= Column(String(50)) 

    message= Column (Text)    

    created_at = Column(DateTime, default=datetime.utcnow)


