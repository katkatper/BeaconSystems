from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from database.connection import Base
from datetime import datetime



class EvidenceChain(Base):

    __tablename__ = "evidence_chain"


    chain_id = Column(Integer, primary_key=True, index=True)


    evidence_id = Column(Integer, ForeignKey("evidence.evidence_id"), nullable=False)

    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)

    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)


    action = Column(String(100), nullable=False)
    from_holder = Column(String(200), nullable=True)
    to_holder = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    available_at = Column(DateTime, nullable=True)

    details = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
