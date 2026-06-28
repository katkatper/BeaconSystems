from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database.connection import get_db
from models import timeline_events
from models.sighting import Sighting
from models.case import Cases
from models.user import User
from security.auth import get_current_user, require_role
from security.case_access import (
    apply_related_case_access_filter,
    assert_case_write_access,
    get_authorized_case,
)
from services.activity_service import create_activity_log 
from schemas.sighting_schema import SightingCreate, SightingUpdate, SightingResponse, MessageResponse
from models.timeline_events import Timeline_Event
from services.alert_service import create_alert
from services.geocoding_service import geocode_address

# CREATE APIRouter INSTANCE WITH PREFIX AND TAGS

router = APIRouter(prefix="/sightings", tags=["Sightings"])


def apply_geocode_metadata(target, geocoded):
    target.geocode_provider = geocoded.get("provider") if geocoded else None
    target.geocode_accuracy = geocoded.get("accuracy") if geocoded else None
    target.geocode_score = geocoded.get("score") if geocoded else None
    target.geocoded_address = geocoded.get("formatted_address") if geocoded else None
    target.geocoded_at = datetime.utcnow() if geocoded else None


@router.get("/test")

def sightings_test():

    return {"message": "Sightings router is working"}


# GET SIGHTINGS WITH OPTIONAL FILTERS AND PAGINATION, LOG ACTIVITY, RETURN LIST OF SIGHTINGS

@router.get("/", response_model=List[SightingResponse])

def get_sightings(
    case_id: Optional[int] = Query(None),

    limit: int = Query(20, ge=1, le=100),

    offset: int = Query(0, ge=0),

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):
    query = db.query(Sighting)
    query = apply_related_case_access_filter(query, Sighting.case_id, current_user)

    if case_id is not None:
        get_authorized_case(db, case_id, current_user)
        query = query.filter(Sighting.case_id == case_id)

    sightings = query.offset(offset).limit(limit).all()
    

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        action="VIEW_SIGHTINGS",

        entity="sighting",

        details=f"{current_user.username} viewed sightings",
    )

    return sightings

# GET SIGHTING BY ID, LOG ACTIVITY, RETURN SIGHTING DETAILS, RAISE 404 IF NOT FOUND

@router.get("/{sighting_id}", response_model=SightingResponse)

def get_sighting_by_id(

    sighting_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),
):

    query = db.query(Sighting).filter(Sighting.sighting_id == sighting_id)
    query = apply_related_case_access_filter(query, Sighting.case_id, current_user)
    sighting = query.first()

    if not sighting:

        raise HTTPException(status_code=404, detail="Sighting not found or access denied")

    return sighting

# CREATE SIGHTING WITH ROLE-BASED ACCESS CONTROL, LOG ACTIVITY, 
# RETURN CREATED SIGHTING ID, RAISE 404 IF CASE NOT FOUND

@router.post("/", response_model=MessageResponse)

def create_sighting(

    data: SightingCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "agency_admin", "investigator", "supervisor")),
):

    assert_case_write_access(db, data.case_id, current_user)
    latitude = data.latitude
    longitude = data.longitude
    geocoded = geocode_address(data.location) if latitude is None or longitude is None else None

    if geocoded:
        latitude = geocoded["latitude"]
        longitude = geocoded["longitude"]

    new_sighting = Sighting(

        case_id=data.case_id,

        person_id=data.person_id,

        location=data.location,

        latitude=latitude,

        longitude=longitude,

        description=data.description,

        confidence_score=data.confidence_score,

        image_url=data.image_url,
    )

    apply_geocode_metadata(new_sighting, geocoded)

    db.add(new_sighting)
    db.commit()
    db.refresh(new_sighting)

    timeline_event = Timeline_Event(

        case_id=new_sighting.case_id,

        person_id=new_sighting.person_id,

        event_type="sighting",

        source_type="user_report",

        location=new_sighting.location,

        description=new_sighting.description,
    )

    db.add(timeline_event)
    db.commit()

    if (
        new_sighting.confidence_score is not None
        and new_sighting.confidence_score >= 0.8
    ):

        create_alert(

            db=db,

            case_id=new_sighting.case_id,

            person_id=new_sighting.person_id,

            recipient_agency_id=current_user.agency_id,

            alert_type="HIGH_CONFIDENCE_SIGHTING",

            title="High Confidence Sighting",

            description=(
                f"High confidence sighting reported at "

                f"{new_sighting.location}"
            ),
            severity="high",
        )

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        action="CREATE",

        entity="sighting",

        entity_id=new_sighting.sighting_id,

        details=f"Sighting created for case {data.case_id}",
    )

    return {
        "message": "Sighting created",
        "sighting_id": new_sighting.sighting_id,
    }
# UPDATE SIGHTING WITH ROLE-BASED ACCESS CONTROL, LOG ACTIVITY, 
# RETURN SUCCESS MESSAGE, RAISE 404 IF SIGHTING NOT FOUND

@router.put("/{sighting_id}", response_model=MessageResponse)

def update_sighting(

    sighting_id: int,

    data: SightingUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "agency_admin", "investigator", "supervisor")),
):

    sighting = db.query(Sighting).filter(Sighting.sighting_id == sighting_id).first()

    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")

    assert_case_write_access(db, sighting.case_id, current_user)

    previous_confidence = sighting.confidence_score

    update_data = data.model_dump(exclude_unset=True)

    if "location" in update_data and (
        update_data.get("latitude") is None or update_data.get("longitude") is None
    ):
        geocoded = geocode_address(update_data.get("location"))

        if geocoded:
            update_data["latitude"] = geocoded["latitude"]
            update_data["longitude"] = geocoded["longitude"]
            update_data["geocode_provider"] = geocoded.get("provider")
            update_data["geocode_accuracy"] = geocoded.get("accuracy")
            update_data["geocode_score"] = geocoded.get("score")
            update_data["geocoded_address"] = geocoded.get("formatted_address")
            update_data["geocoded_at"] = datetime.utcnow()
        else:
            update_data["latitude"] = None
            update_data["longitude"] = None
            update_data["geocode_provider"] = None
            update_data["geocode_accuracy"] = None
            update_data["geocode_score"] = None
            update_data["geocoded_address"] = None
            update_data["geocoded_at"] = None

    for field, value in update_data.items():
        setattr(sighting, field, value)

    db.commit()
    db.refresh(sighting)

    if (
        sighting.confidence_score is not None
        and sighting.confidence_score >= 0.8
        and (
            previous_confidence is None
            or previous_confidence < 0.8
        )
    ):

        create_alert(
            db=db,
            case_id=sighting.case_id,
            person_id=sighting.person_id,
            recipient_agency_id=current_user.agency_id,
            alert_type="SIGHTING_ESCALATED",
            title="Sighting Escalated",
            description=(
                f"Sighting at {sighting.location} "
                f"was escalated to high confidence."
            ),
            severity="high",
        )

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        action="UPDATE",

        entity="sighting",

        entity_id=sighting.sighting_id,

        details=f"Sighting {sighting.sighting_id} updated",
    )

    return {"message": "Sighting updated"}

# DELETE SIGHTING WITH ROLE-BASED ACCESS CONTROL, LOG ACTIVITY,
# RETURN SUCCESS MESSAGE, RAISE 404 IF SIGHTING NOT FOUND

@router.delete("/{sighting_id}", response_model=MessageResponse)

def delete_sighting(

    sighting_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "agency_admin", "investigator", "supervisor")),
):

    sighting = db.query(Sighting).filter(Sighting.sighting_id == sighting_id).first()

    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")

    assert_case_write_access(db, sighting.case_id, current_user)

    sighting_id_value = sighting.sighting_id

    create_alert(
        db=db,
        case_id=sighting.case_id,
        person_id=sighting.person_id,
        recipient_agency_id=current_user.agency_id,
        alert_type="SIGHTING_DELETED_AUDIT",
        title="Sighting Deleted",
        description=f"Sighting at {sighting.location} was deleted.",
        severity="medium",
    )

    db.delete(sighting)
    db.commit()

    create_activity_log(

        db=db,

        user_id=current_user.user_id,

        action="DELETE",

        entity="sighting",

        entity_id=sighting_id_value,

        details=f"Sighting {sighting_id_value} deleted",
    )

    return {"message": "Sighting deleted"}
