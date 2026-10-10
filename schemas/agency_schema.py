from pydantic import BaseModel, ConfigDict


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
