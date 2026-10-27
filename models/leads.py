from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text

from database.connection import Base


class Leads(Base):

    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_case_status", "case_id", "status"),
        Index("ix_leads_assignee_status", "assigned_to_user_id", "status"),
    )

    lead_id = Column(Integer, primary_key=True)

    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True)

    lead_source= Column(String(100))

    description= Column(Text)

    confidence_score= Column(Float)

    status = Column(String(50), nullable=False, default="new")

    priority = Column(String(20), nullable=False, default="medium")

    assigned_to_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    due_at = Column(DateTime, nullable=True)

    resolution = Column(Text, nullable=True)

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    closed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

