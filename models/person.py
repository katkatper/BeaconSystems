from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from database.connection import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class Person(Base):
    __tablename__ = "persons"

    person_id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    age = Column(Integer, nullable=True)

    eye_color = Column(String(20), nullable=True)
    hair_color = Column(String(20), nullable=True)

    height = Column(String(20), nullable=True)
    weight = Column(Float, nullable=True)

    scars = Column(Text, nullable=True)
    tattoos = Column(Text, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    criminal_arrests_count = Column(Integer, default=0, nullable=True)
    felony_convictions_count = Column(Integer, default=0, nullable=True)
    active_warrants_count = Column(Integer, default=0, nullable=True)
    protective_orders_count = Column(Integer, default=0, nullable=True)
    last_arrest_date = Column(DateTime, nullable=True)
    most_serious_offense = Column(String(255), nullable=True)
    criminal_history = Column(Text, nullable=True)
    warrants = Column(Text, nullable=True)
    arrests = Column(Text, nullable=True)
    charges = Column(Text, nullable=True)
    convictions = Column(Text, nullable=True)
    corrections_history = Column(Text, nullable=True)
    known_associates = Column(Text, nullable=True)
    gang_affiliations = Column(Text, nullable=True)
    vehicles = Column(Text, nullable=True)
    addresses = Column(Text, nullable=True)
    tips = Column(Text, nullable=True)
    patterns = Column(Text, nullable=True)
    intelligence_notes = Column(Text, nullable=True)

    dna_profile_id = Column(Integer, nullable=True)
    photo_url = Column(Text, nullable=True)

    last_seen_location = Column(Text, nullable=True)
    last_seen_date = Column(DateTime, nullable=True)

    risk_level = Column(String(20), default="medium")
    status = Column(String(20), default="missing")

    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    cases= relationship("Cases", back_populates="person")
