from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from database.connection import Base


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        Index("ix_matches_agency_status_created", "agency_id", "status", "created_at"),
        UniqueConstraint(
            "agency_id",
            "person_id",
            "external_record_id",
            name="uq_matches_agency_person_record",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    agency_id = Column(Integer, ForeignKey("agencies.agency_id"), nullable=False, index=True)


    person_id = Column(Integer, ForeignKey("persons.person_id"))

    external_record_id = Column(Integer, ForeignKey("external_records.id"))


    score = Column(Integer, nullable=False)

    status = Column(String, nullable=False, default="pending_review")

    disposition_reason = Column(Text, nullable=True)

    reviewed_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    created_at = Column(DateTime(timezone=True), server_default=func.now())
