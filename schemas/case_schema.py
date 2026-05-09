from typing import Optional
from pydantic import BaseModel  



class CaseCreate(BaseModel):

    case_number: str

    person_id: Optional[int] = None

    description: Optional[str] = None 

    investigator_id: Optional[int] = None   

    reporting_agency_id: Optional[int] = None   

    last_seen_location: Optional[str] = None

    priority_level: Optional[str] = None    

    notes: Optional[str] = None

    case_status: Optional[str] = "open"


class CaseUpdate(BaseModel):

 case_number: Optional[str] = None

person_id: Optional[int] = None

description: Optional[str] = None 

investigator_id: Optional[int] = None  

reporting_agency_id: Optional[int] = None
 
last_seen_location: Optional[str] = None

priority_level: Optional[str] = None    

notes: Optional[str] = None

case_status: Optional[str] = None


class CaseResponse(BaseModel):

    case_id: int

    case_number: Optional[str] = None

    person_id: Optional[int] = None

    investigator_id: Optional[int] = None

    reporting_agency_id: Optional[int] = None

    last_seen_location: Optional[str] = None

    priority_level: Optional[str] = None

    notes: Optional[str] = None

    case_status: Optional[str] = None   



    class config:
        from_attributes=True


class CaseCreateResponse(BaseModel):

            message: str

            case_id: int


class MessageResponse(BaseModel):

    message: str

