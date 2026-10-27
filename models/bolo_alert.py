from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text

from database.connection import Base


class BoloAlert(Base):
    __tablename__ = "bolo_alerts"
    __table_args__ = (
        Index("ix_bolo_alerts_agency_status_created", "agency_id", "status", "created_at"),
        Index(
            "ix_bolo_alerts_agency_status_plate",
            "agency_id",
            "status",
            "plate_number",
            "plate_state",
        ),
        Index(
            "ix_bolo_alerts_agency_status_vehicle",
            "agency_id",
            "status",
            "vehicle_make",
            "vehicle_model",
            "vehicle_color",
        ),
    )

    bolo_id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    title = Column(String(255), nullable=False)
    person_name = Column(String(255), nullable=True)
    last_known_location = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geocode_provider = Column(String(50), nullable=True)
    geocode_accuracy = Column(String(50), nullable=True)
    geocode_score = Column(Float, nullable=True)
    geocoded_address = Column(String(500), nullable=True)
    geocoded_at = Column(DateTime, nullable=True)
    description = Column(Text, nullable=False)
    vehicle_year = Column(Integer, nullable=True)
    vehicle_make = Column(String(100), nullable=True)
    vehicle_model = Column(String(100), nullable=True)
    vehicle_color = Column(String(100), nullable=True)
    plate_number = Column(String(32), nullable=True)
    plate_state = Column(String(16), nullable=True)
    vehicle_identifiers = Column(Text, nullable=True)
    risk_level = Column(String(50), default="high", nullable=False)
    status = Column(String(50), default="active", nullable=False)

    share_with_partners = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
