from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from database.connection import Base


class AccountInvitation(Base):
    __tablename__ = "account_invitations"

    token_hash = Column(String(64), primary_key=True)
    email = Column(String(254), nullable=False)
    role = Column(String(32), nullable=False)
    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=False)
    issuer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)


class AccountAccessRequest(Base):
    __tablename__ = "account_access_requests"

    request_id = Column(Integer, primary_key=True)
    email = Column(String(254), nullable=False)
    agency_name = Column(String(200), nullable=False)
    created_at = Column(DateTime, nullable=False)
    reviewed_at = Column(DateTime)
    decision = Column(String(16))
