from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint

from database.connection import Base


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"
    __table_args__ = (
        UniqueConstraint("alert_id", "agency_id", name="uq_alert_deliveries_alert_agency"),
        Index("ix_alert_deliveries_agency_status", "agency_id", "status", "created_at"),
    )

    delivery_id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.alert_id"), nullable=False)
    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    viewed_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
