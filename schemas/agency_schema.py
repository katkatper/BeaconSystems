from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AgencyCreate(BaseModel):
    agency_name: str = Field(min_length=2, max_length=200)
    agency_type: str = Field(min_length=2, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str = Field(min_length=2, max_length=100)
    contact_phone: str | None = Field(default=None, max_length=50)
    contact_email: EmailStr | None = None


class AgencyStatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|suspended|offboarded)$")
    reason: str = Field(min_length=10, max_length=1000)


class AgencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agency_id: int
    agency_name: str | None = None
    agency_type: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    lifecycle_status: str
    status_changed_at: datetime | None = None
    status_reason: str | None = None
