from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from database.connection import Base
from datetime import datetime




class Evidence(Base):

    __tablename__ = "evidence"


    evidence_id = Column(Integer, primary_key=True, index=True)


    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)


    description = Column(Text, nullable=True)
    evidence_type = Column(String(100), nullable=False)



    collected_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    evidence_location = Column(String(200), nullable=True)
    custody_status = Column(String(100), default="collected")
    current_holder = Column(String(200), nullable=True)
    lab_reference = Column(String(200), nullable=True)
    available_at = Column(DateTime, nullable=True)

    is_sensitive = Column(Boolean, default=False)

    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)



    collected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
