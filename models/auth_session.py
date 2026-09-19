from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from database.connection import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    session_id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    refresh_token_hash = Column(String(64), nullable=True, unique=True, index=True)
    refresh_expires_at = Column(DateTime, nullable=True, index=True)
