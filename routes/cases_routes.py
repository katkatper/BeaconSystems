from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from services.activity_service import log_activity
from database.connection import get_db
from models.case import Cases
from models.user import User
from security.auth import get_current_user, require_role
from schemas.case_schema import CaseCreate, CaseUpdate, CaseResponse, CaseCreateResponse, MessageResponse
from typing import List, Optional

router = APIRouter(prefix="/cases", tags=["Cases"])



@router.get("/by-person/{person_id}", response_model=List[CaseResponse])
def get_cases_by_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Cases).filter(Cases.person_id == person_id)

    if current_user.role != "admin":
        query = query.filter(Cases.investigator_id == current_user.user_id)

    return query.all()


# temp test route to verify router is working, remove later

@router.get("/test")
def get_cases_test():

    return [
        {"case_id": 1, "case_number": "B-1001", "case_status": "Open"},
        {"case_id": 2, "case_number": "B-1002", "case_status": "Investigating"},
    ]


@router.get("/", response_model=List[CaseResponse])

def get_cases(
    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

    case_status: Optional[str] = Query(None),

    priority_level: Optional[str] = Query(None),

    investigator_id: Optional[int] = Query(None),

    limit: int = Query(20, ge=1, le=100),

    offset: int = Query(0, ge=0),
):
    query = db.query(Cases)

    if current_user.role != "admin":
        query = query.filter(Cases.investigator_id == current_user.user_id)

    if case_status:
        query = query.filter(Cases.case_status == case_status)

    if priority_level:
        query = query.filter(Cases.priority_level == priority_level)

    if investigator_id is not None and current_user.role == "admin":
        query = query.filter(Cases.investigator_id == investigator_id)

    cases = query.offset(offset).limit(limit).all()

    log_activity(
        db=db,

        user_id=current_user.user_id,

        action="VIEW_CASES",

        entity="case",

        details=f"{current_user.username} viewed accessible cases with filters",
    )

    return cases


# CREATE CASE WITH ROLE-BASED ACCESS CONTROL AND ACTIVITY LOGGING

@router.post("/", response_model=CaseCreateResponse)

def create_case(

    data: CaseCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "investigator"))
):
    investigator_id = data.investigator_id


    if current_user.role != "admin":

        investigator_id = current_user.user_id

    new_case = Cases(

        case_number=data.case_number,

        person_id=data.person_id,

        description=data.description,

        investigator_id=investigator_id,

        reporting_agency_id=data.reporting_agency_id,

        last_seen_location=data.last_seen_location,

        priority_level=data.priority_level,

        notes=data.notes,

        case_status=data.case_status or "open",
    )

    db.add(new_case)

    db.commit()

    db.refresh(new_case)


    log_activity(

        db=db,

        user_id=current_user.user_id,

        action="CREATE",

        entity="case",

        entity_id=new_case.case_id,

        details=f"Case {new_case.case_number} created",
    )

    return {"message": "Case created", "case_id": new_case.case_id}


# UPDATE CASE WITH ROLE-BASED ACCESS CONTROL AND ACTIVITY LOGGING

@router.get("/{case_id}", response_model=CaseResponse)
def get_case_by_id(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(Cases).filter(Cases.case_id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if current_user.role != "admin" and case.investigator_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return case


@router.put("/{case_id}", response_model=MessageResponse)

def update_case(

    case_id: int,

    data: CaseUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "investigator"))
):

    case = db.query(Cases).filter(Cases.case_id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if current_user.role != "admin" and case.investigator_id != current_user.user_id:

        log_activity(

            db=db,

            user_id=current_user.user_id,

            action="UNAUTHORIZED_ACCESS",

            entity="case",

            entity_id=case.case_id,

            details=f"{current_user.username} tried to update restricted case {case.case_number}",
        )
        raise HTTPException(status_code=403, detail="Access denied")


    update_data= data.model_dump(exclude_unset=True)    

    if current_user.role != "admin":

        update_data.pop("investigator_id", None)


    for field, value in update_data.items():

        setattr(case, field, value)

    db.commit()

    db.refresh(case)


    log_activity(

        db=db,

        user_id=current_user.user_id,

        action="UPDATE",

        entity="case",

        entity_id=case.case_id,

        details=f"Updated case {case.case_number}",
    )

    return {"message": "Case updated"}

# DELETE CASE WITH ROLE-BASED ACCESS CONTROL AND ACTIVITY LOGGING


@router.delete("/{case_id}", response_model=MessageResponse)

def delete_case(

    case_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(require_role("admin", "investigator"))
):
    case = db.query(Cases).filter(Cases.case_id == case_id).first()


    if not case:
        raise HTTPException(status_code=404, detail="Case not found")


    if current_user.role != "admin" and case.investigator_id != current_user.user_id:

        log_activity(

            db=db,

            user_id=current_user.user_id,

            action="UNAUTHORIZED_ACCESS",

            entity="case",

            entity_id=case.case_id,

            details=f"{current_user.username} tried to delete restricted case {case.case_number}",
        )

        raise HTTPException(status_code=403, detail="Access denied")

    case_number = case.case_number

    case_id_value = case.case_id

    db.delete(case)

    db.commit()

    log_activity(

        db=db,

        user_id=current_user.user_id,

        action="DELETE",

        entity="case",

        entity_id=case_id_value,

        details=f"Deleted case {case_number}",

    )

    return {"message": "Case deleted"}

# CASE SUMMARY ENDPOINT WITH AGGREGATED COUNTS AND ACTIVITY LOGGING


@router.get("/summary/counts", response_model=dict)

def get_case_counts(

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):
    query = db.query(Cases)


    if current_user.role != "admin":

        query = query.filter(Cases.investigator_id == current_user.user_id)

    total = query.count()

    open_count = query.filter(Cases.case_status == "open").count()

    closed_count = query.filter(Cases.case_status == "closed").count()

    high_priority = query.filter(Cases.priority_level == "high").count()


    log_activity(

        db=db,

        user_id=current_user.user_id,

        action="VIEW_CASE_SUMMARY",

        entity="case",

        details=f"{current_user.username} viewed case summary counts",

    )

    return {

        "total": total,

        "open": open_count,

        "closed": closed_count,

        "high_priority": high_priority,
    }