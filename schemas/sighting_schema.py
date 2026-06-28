from typing import Optional
from pydantic import BaseModel
from datetime import datetime

#PYDANTIC MODELS FOR SIGHTINGS

class SightingCreate(BaseModel):

    case_id: int

    person_id: Optional[int] = None

    location: str

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    description: Optional[str] = None

    confidence_score: Optional[float] = None

    image_url: Optional[str] = None


 #ADD VALIDATION FOR CONFIDENCE SCORE TO BE BETWEEN 0 AND 1

class SightingUpdate(BaseModel):

    location: Optional[str] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    description: Optional[str] = None

    confidence_score: Optional[float] = None

    image_url: Optional[str] = None


class SightingResponse(BaseModel):

    sighting_id: int

    case_id: int

    person_id: Optional[int] = None

    location: Optional[str] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    geocode_provider: Optional[str] = None

    geocode_accuracy: Optional[str] = None

    geocode_score: Optional[float] = None

    geocoded_address: Optional[str] = None

    geocoded_at: Optional[datetime] = None
    
    sighting_time: Optional[datetime] = None

    description: Optional[str] = None

    confidence_score: Optional[float] = None

    created_at: Optional[datetime] = None


    class Config:

        from_attributes = True


class MessageResponse(BaseModel):

    message: str

    sighting_id: Optional[int] = None

