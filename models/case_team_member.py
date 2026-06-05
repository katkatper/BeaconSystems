from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from database.connection import Base


class CaseTeamMember(Base):
    __tablename__ = "case_team_members"

    team_member_id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=True)

    role = Column(String(50), default="support_investigator", nullable=False)
    status = Column(String(50), default="active", nullable=False)
    reason = Column(Text, nullable=True)
    assigned_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    removed_at = Column(DateTime, nullable=True)
