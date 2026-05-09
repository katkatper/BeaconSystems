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