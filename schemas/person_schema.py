from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PersonCreate(BaseModel):

    first_name: str

    last_name: str

    age: Optional[int] = None

    eye_color: Optional[str] = None

    hair_color: Optional[str] = None

    height: Optional[str] = None

    weight: Optional[float] = None

    scars: Optional[str] = None

    tattoos: Optional[str] = None

    medical_conditions: Optional[str] = None

    primary_address: Optional[str] = None

    housing_status: Optional[str] = None

    school_name: Optional[str] = None

    school_address: Optional[str] = None

    employer_name: Optional[str] = None

    work_address: Optional[str] = None

    employment_status: Optional[str] = None

    criminal_arrests_count: Optional[int] = 0

    felony_convictions_count: Optional[int] = 0

    active_warrants_count: Optional[int] = 0

    protective_orders_count: Optional[int] = 0

    last_arrest_date: Optional[datetime] = None

    most_serious_offense: Optional[str] = None

    criminal_history: Optional[str] = None

    warrants: Optional[str] = None

    arrests: Optional[str] = None

    charges: Optional[str] = None

    convictions: Optional[str] = None

    corrections_history: Optional[str] = None

    known_associates: Optional[str] = None

    gang_affiliations: Optional[str] = None

    vehicles: Optional[str] = None

    addresses: Optional[str] = None

    tips: Optional[str] = None

    patterns: Optional[str] = None

    intelligence_notes: Optional[str] = None

    dna_profile_id: Optional[int] = None

    photo_url: Optional[str] = None

    last_seen_location: Optional[str] = None

    last_seen_date: Optional[datetime] = None

    risk_level: Optional[str] = "medium"

    status: Optional[str] = "missing"

    description: Optional[str] = None


class PersonUpdate(BaseModel):

    first_name: Optional[str] = None

    last_name: Optional[str] = None

    age: Optional[int] = None

    eye_color: Optional[str] = None

    hair_color: Optional[str] = None

    height: Optional[str] = None

    weight: Optional[float] = None

    scars: Optional[str] = None

    tattoos: Optional[str] = None

    medical_conditions: Optional[str] = None

    primary_address: Optional[str] = None

    housing_status: Optional[str] = None

    school_name: Optional[str] = None

    school_address: Optional[str] = None

    employer_name: Optional[str] = None

    work_address: Optional[str] = None

    employment_status: Optional[str] = None

    criminal_arrests_count: Optional[int] = None

    felony_convictions_count: Optional[int] = None

    active_warrants_count: Optional[int] = None

    protective_orders_count: Optional[int] = None

    last_arrest_date: Optional[datetime] = None

    most_serious_offense: Optional[str] = None

    criminal_history: Optional[str] = None

    warrants: Optional[str] = None

    arrests: Optional[str] = None

    charges: Optional[str] = None

    convictions: Optional[str] = None

    corrections_history: Optional[str] = None

    known_associates: Optional[str] = None

    gang_affiliations: Optional[str] = None

    vehicles: Optional[str] = None

    addresses: Optional[str] = None

    tips: Optional[str] = None

    patterns: Optional[str] = None

    intelligence_notes: Optional[str] = None

    dna_profile_id: Optional[int] = None

    photo_url: Optional[str] = None

    last_seen_location: Optional[str] = None

    last_seen_date: Optional[datetime] = None

    risk_level: Optional[str] = None

    status: Optional[str] = None

    description: Optional[str] = None


class PersonResponse(BaseModel):

    person_id: int

    first_name: str

    last_name: str

    age: Optional[int] = None

    eye_color: Optional[str] = None

    hair_color: Optional[str] = None

    height: Optional[str] = None

    weight: Optional[float] = None

    scars: Optional[str] = None

    tattoos: Optional[str] = None

    medical_conditions: Optional[str] = None

    primary_address: Optional[str] = None

    housing_status: Optional[str] = None

    school_name: Optional[str] = None

    school_address: Optional[str] = None

    employer_name: Optional[str] = None

    work_address: Optional[str] = None

    employment_status: Optional[str] = None

    criminal_arrests_count: Optional[int] = None

    felony_convictions_count: Optional[int] = None

    active_warrants_count: Optional[int] = None

    protective_orders_count: Optional[int] = None

    last_arrest_date: Optional[datetime] = None

    most_serious_offense: Optional[str] = None

    criminal_history: Optional[str] = None

    warrants: Optional[str] = None

    arrests: Optional[str] = None

    charges: Optional[str] = None

    convictions: Optional[str] = None

    corrections_history: Optional[str] = None

    known_associates: Optional[str] = None

    gang_affiliations: Optional[str] = None

    vehicles: Optional[str] = None

    addresses: Optional[str] = None

    tips: Optional[str] = None

    patterns: Optional[str] = None

    intelligence_notes: Optional[str] = None

    dna_profile_id: Optional[int] = None

    photo_url: Optional[str] = None

    last_seen_location: Optional[str] = None

    last_seen_date: Optional[datetime] = None

    risk_level: Optional[str] = None

    status: Optional[str] = None

    description: Optional[str] = None

    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str
    person_id: Optional[int] = None
    case_id: Optional[int] = None
    case_number: Optional[str] = None
